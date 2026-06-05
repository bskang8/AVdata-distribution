"""
vLLM 서버(OpenAI 호환 API)를 통한 cosmos-reason2 비동기 클라이언트.

영상 입력 방식:
  VIDEO_INPUT_MODE="frames" : 균등 샘플링 프레임을 image_url 배열로 전달
  VIDEO_INPUT_MODE="video"  : MP4 전체를 base64로 직렬화해 video_url 한 개로 전달
"""
import asyncio
import base64
import io
import json
import logging
import re
from pathlib import Path

import cv2
import numpy as np
from openai import AsyncOpenAI, APIError, APITimeoutError

from caption_refine.config import (
    FRAME_QUALITY,
    MAX_FRAME_H,
    MAX_FRAME_W,
    MAX_RETRIES,
    MAX_TOKENS_STAGE12,
    MAX_TOKENS_STAGE3,
    MAX_TOKENS_STAGE4,
    NUM_FRAMES,
    REQUEST_TIMEOUT,
    RETRY_DELAY_BASE,
    VIDEO_INPUT_MODE,
    VLLM_API_KEY,
    VLLM_BASE_URL,
    VLLM_MODEL,
)
from caption_refine.prompts import SYSTEM_PROMPT

log = logging.getLogger(__name__)


# ── 프레임 유틸 ───────────────────────────────────────────────────────────────

def _resize_frame(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    if w > MAX_FRAME_W or h > MAX_FRAME_H:
        scale = min(MAX_FRAME_W / w, MAX_FRAME_H / h)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return frame


def sample_frames(video_path: str | Path, n: int = NUM_FRAMES) -> list[np.ndarray]:
    """MP4에서 n 프레임을 균등 샘플링해 BGR ndarray 목록으로 반환."""
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        cap.release()
        raise ValueError(f"No frames found in {video_path}")

    indices = np.linspace(0, max(total - 1, 0), min(n, total), dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if ok:
            frames.append(_resize_frame(frame))
    cap.release()

    if not frames:
        raise ValueError(f"Failed to decode any frame from {video_path}")
    return frames


def _frame_to_b64(frame: np.ndarray) -> str:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return base64.b64encode(buf.tobytes()).decode()


def _video_to_b64(video_path: str | Path) -> str:
    return base64.b64encode(Path(video_path).read_bytes()).decode()


# ── content 블록 빌더 ─────────────────────────────────────────────────────────

def _build_content(video_path: str | Path, prompt: str) -> list[dict]:
    """VIDEO_INPUT_MODE에 따라 멀티모달 content 블록 구성."""
    if VIDEO_INPUT_MODE == "video":
        b64 = _video_to_b64(video_path)
        return [
            {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]
    else:  # "frames" (default)
        frames = sample_frames(video_path)
        content: list[dict] = []
        for frame in frames:
            b64 = _frame_to_b64(frame)
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        content.append({"type": "text", "text": prompt})
        return content


# ── JSON 파싱 헬퍼 ────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | list:
    """응답 텍스트에서 JSON을 추출. 마크다운 코드블록 포함 처리."""
    text = text.strip()

    # ```json ... ``` 또는 ``` ... ``` 제거
    md = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if md:
        text = md.group(1).strip()

    # 첫 번째 { 또는 [ 부터 파싱 시도
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start != -1:
            # 마지막 닫는 괄호 찾기
            end = text.rfind(end_char)
            if end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

    raise ValueError(f"No valid JSON found in response: {text[:200]}")


# ── 메인 클라이언트 ───────────────────────────────────────────────────────────

class CosmosClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=VLLM_BASE_URL,
            api_key=VLLM_API_KEY,
            timeout=REQUEST_TIMEOUT,
        )

    async def _chat(
        self,
        video_path: str | Path,
        prompt: str,
        max_tokens: int,
    ) -> str:
        """vLLM에 요청을 보내고 응답 텍스트를 반환. 재시도 포함."""
        content = await asyncio.get_event_loop().run_in_executor(
            None, _build_content, video_path, prompt
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": content},
        ]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await self._client.chat.completions.create(
                    model=VLLM_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.0,
                )
                return resp.choices[0].message.content or ""
            except (APIError, APITimeoutError) as exc:
                if attempt == MAX_RETRIES:
                    raise
                delay = RETRY_DELAY_BASE ** attempt
                log.warning("API error (attempt %d/%d): %s — retrying in %.1fs",
                            attempt, MAX_RETRIES, exc, delay)
                await asyncio.sleep(delay)
        return ""  # unreachable

    async def chat_json(
        self,
        video_path: str | Path,
        prompt: str,
        max_tokens: int = MAX_TOKENS_STAGE12,
    ) -> dict | list:
        """JSON 응답이 필요한 Stage 1·2·3 전용. 파싱 실패 시 재시도."""
        for attempt in range(1, MAX_RETRIES + 1):
            raw = await self._chat(video_path, prompt, max_tokens)
            try:
                return _extract_json(raw)
            except ValueError as exc:
                if attempt == MAX_RETRIES:
                    log.error("JSON parse failed after %d attempts: %s\nraw=%s",
                              MAX_RETRIES, exc, raw[:300])
                    raise
                log.warning("JSON parse failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
                await asyncio.sleep(RETRY_DELAY_BASE)

    async def chat_text(
        self,
        video_path: str | Path,
        prompt: str,
        max_tokens: int = MAX_TOKENS_STAGE4,
    ) -> str:
        """텍스트 응답이 필요한 Stage 4 전용."""
        return await self._chat(video_path, prompt, max_tokens)

    async def aclose(self) -> None:
        await self._client.close()
