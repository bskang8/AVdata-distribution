# caption_refine 파이프라인 상세 설명

## 목적

기존 캡션(1차 AI 생성)은 두 가지 문제를 가지고 있습니다.

1. **Hallucination** — 영상에 없는 내용이 캡션에 기술되어 있음
2. **정보 부족** — 날씨, 차선 수, 신호 상태, 보행자 행동 등 ODD 분석에 필요한 세부 정보가 누락되어 있음

`caption_refine`은 cosmos-reason2 비전-언어 모델을 통해 영상을 직접 보면서 캡션을 검증하고 정제하는 **4-Stage 파이프라인**입니다.

---

## 전체 구조

```
src/caption_refine/
├── config.py           전역 설정 (경로, 모델, 파라미터)
├── prompts.py          4개 Stage 프롬프트 템플릿
├── cosmos_client.py    vLLM API 클라이언트 + 영상 프레임 변환
├── stages/
│   ├── stage1_ground.py    Stage 1: 기존 캡션 검증
│   ├── stage2_extract.py   Stage 2: ODD 정보 추출
│   ├── stage3_verify.py    Stage 3: 저확신 항목 재검증
│   └── stage4_refine.py    Stage 4: 정제 캡션 생성
├── pipeline.py         단일 클립 4-Stage 오케스트레이션
└── batch_runner.py     배치 처리 + 진행 추적
```

출력 경로:
```
/Data1/home/bskang/cds-data/caption_v2/
├── captions/{clip_id}.camera_front_wide_120fov.txt   정제된 캡션
├── odd/{clip_id}.json                                구조화된 ODD 정보
├── diff/{clip_id}_diff.json                          변경 내역 기록
└── progress.json                                     처리 진행 상태
```

---

## 실행 방법

```bash
# 환경변수로 vLLM 서버 지정
export CR_VLLM_URL="http://localhost:8080/v1"
export CR_VLLM_MODEL="nvidia/Cosmos-Reason2-7B"

# SANFlow 갭 클립 200개 처리 (권장 첫 시작)
uv run python -m caption_refine.batch_runner --source gap

# Long-tail 클립 처리
uv run python -m caption_refine.batch_runner --source longtail

# 전체 29만 클립 처리 (limit으로 부분 처리 가능)
uv run python -m caption_refine.batch_runner --source all --limit 5000

# 특정 clip_id 목록 파일로 처리
uv run python -m caption_refine.batch_runner --ids-file my_clips.json

# 동시 처리 수 조정 (vLLM 서버 용량에 맞게)
uv run python -m caption_refine.batch_runner --source gap --concurrent 4

# 진행 상태 초기화 후 처음부터 재시작
uv run python -m caption_refine.batch_runner --source gap --reset
```

---

## 주요 설정값 (config.py)

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `CR_VLLM_URL` | `http://localhost:8080/v1` | vLLM 서버 주소 |
| `CR_VLLM_MODEL` | `nvidia/Cosmos-Reason2-7B` | 모델 이름 |
| `CR_VIDEO_MODE` | `frames` | `frames`(16장 이미지) 또는 `video`(MP4 통째) |
| `CR_NUM_FRAMES` | `16` | 영상에서 추출할 프레임 수 |
| `CR_CONF_THRESHOLD` | `0.7` | Stage 3 재검증 기준 confidence |
| `CR_CONCURRENT` | `2` | 동시에 처리할 클립 수 |

---

## 전체 흐름도

```
batch_runner.py 실행
│
├─ clip_id 목록 로드 (gap / longtail / all / ids-file)
├─ progress.json 읽기 → 이미 처리된 클립 제외
│
├─ asyncio.Semaphore(N)로 동시 처리 수 제한
│
├─ [Clip A] process_clip()          [Clip B] process_clip()
│     │                                   │
│     ├─ Stage 1: 캡션 검증               ├─ Stage 1: 캡션 검증
│     ├─ Stage 2: ODD 추출               ├─ Stage 2: ODD 추출
│     ├─ Stage 3: 재검증                 ├─ Stage 3: 재검증
│     └─ Stage 4: 캡션 정제             └─ Stage 4: 캡션 정제
│           │                                   │
│     파일 저장                           파일 저장
│
└─ 10개마다 progress.json 저장 → 중단/재시작 가능
```

---

## 영상 → API 변환 상세 (cosmos_client.py)

cosmos-reason2는 텍스트만 받는 LLM이 아닙니다. 영상 프레임을 함께 입력으로 받는 **비전-언어 모델**입니다. 그러나 HTTP API는 바이너리 파일을 직접 전송할 수 없으므로, 영상을 이미지 배열로 변환해서 전달합니다.

### frames 모드 (기본)

```
MP4 파일 (예: 300 프레임, 30fps, 10초 영상)
│
▼  cv2.VideoCapture 로 열기
총 프레임 수 파악 (300개)
│
▼  np.linspace(0, 299, 16) → [0, 20, 40, 60, ..., 299]
영상 전체에서 균등 간격 16개 프레임 선택
(처음·중간·끝을 골고루 커버)
│
▼  각 프레임 리사이즈 (854×480 이하)
│
▼  JPEG 압축 (품질 85)
│
▼  base64 인코딩
16개의 base64 문자열 생성 (각 약 97KB)
│
▼  OpenAI API content 배열로 조립
[
  {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/..."}},  ← 프레임 1
  {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/..."}},  ← 프레임 2
  ...                                                                               (16개)
  {"type": "text", "text": "Watch this driving video carefully..."}                ← 프롬프트
]
│
▼  vLLM 서버로 POST
cosmos-reason2가 이미지 시퀀스를 시간축 영상으로 해석해 처리
```

> **왜 16프레임인가?**
> 10초짜리 영상을 매 프레임(300개)으로 전달하면 API 페이로드가 수백MB에 달해 비현실적입니다.
> 16프레임은 영상의 시작·경과·끝을 균등하게 포착하면서 페이로드를 ~1.5MB로 유지하는 균형점입니다.
> 필요에 따라 `CR_NUM_FRAMES` 환경변수로 조정할 수 있습니다.

### video 모드 (선택)

```bash
export CR_VIDEO_MODE=video
```

MP4 파일 전체를 base64로 직렬화해 `video_url` 한 개로 전달합니다.
vLLM이 native video input을 지원하고 cosmos-reason2가 전체 프레임을 처리할 수 있을 때 사용합니다.
파일 크기가 크므로 네트워크·메모리 부담이 증가합니다.

---

## Stage 1 — 기존 캡션 검증 (stage1_ground.py)

### 목적

1차 AI가 생성한 캡션에서 실제 영상에 없는 내용(hallucination)과 영상에 있는데 누락된 내용을 찾아냅니다.

### 입력

- 영상 16프레임
- 기존 캡션 전문 (평균 219단어)

### 프롬프트 핵심 구조

```
"기존 캡션을 영상과 비교해서 아래 3가지를 JSON으로 반환하세요:
  grounded    : 영상에서 확인된 캡션 문장
  hallucinated: 영상에 없는데 캡션에 있는 내용
  missed      : 영상에 있는데 캡션에 빠진 내용"
```

### 예시 응답

```json
{
  "grounded": [
    "The ego-vehicle slows down and maneuvers around a stalled car on the left side.",
    "Two pedestrians are crossing at the intersection."
  ],
  "hallucinated": [
    "Heavy rain was falling throughout the entire clip."
  ],
  "missed": [
    "A traffic signal turns from green to red mid-clip.",
    "A bus is visible stopped at a bus stop on the right."
  ]
}
```

이 결과는 `GroundingResult` dataclass에 담겨 Stage 4로 전달됩니다.

---

## Stage 2 — ODD 정보 추출 (stage2_extract.py)

### 목적

영상에서 15개 ODD 필드를 **구조화된 JSON**으로 추출합니다. 각 필드에 **confidence(0~1)** 와 **evidence(근거)** 를 함께 요청해, 모델이 얼마나 확신하는지 기록합니다.

### 입력

- 영상 16프레임만 (기존 캡션 미포함 — 캡션에 의한 편향 방지)

### 추출 필드 목록

| 필드 | 추출 내용 | 기존 odd_tags와 비교 |
|------|----------|---------------------|
| `time_of_day` | day / night / dawn / dusk / unknown | 동일 |
| `weather` | clear / cloudy / rainy / foggy / snowy / unknown | 동일 |
| `road_type` | highway / urban / intersection / rural / parking_lot / tunnel / bridge / unknown | 동일 |
| `num_lanes` | 차선 수 (정수) | **신규** |
| `ego_lane_position` | 자차 차선 위치 (leftmost ~ rightmost) | **신규** |
| `road_surface` | dry / wet / icy / unpaved / unknown | **신규** |
| `road_markings` | 차선, 횡단보도, 정지선, 방향화살표 등 | **신규** |
| `traffic_density` | free / light / moderate / congested / unknown | 동일 |
| `surrounding_vehicles` | 차종, 대수, 주목할 행동 | agent_type 확장 |
| `ego_actions` | straight / braking / lane_change / ... | 동일 |
| `pedestrians` | 유무, 수, 행동 | **신규 세부화** |
| `traffic_signals` | 신호등 유무, 색상 | **신규** |
| `road_signs` | 표지판 종류, 내용 | **신규** |
| `hazard_level` | low / medium / high / unknown + 근거 | 동일 |
| `lighting_condition` | daylight / artificial / mixed / dark / unknown | **신규** |

### 예시 응답

```json
{
  "time_of_day": {
    "value": "day",
    "confidence": 0.95,
    "evidence": "Bright sunlight casts sharp shadows on the road surface."
  },
  "weather": {
    "value": "clear",
    "confidence": 0.55,
    "evidence": "No rain visible on lens but upper sky partially obscured by clouds."
  },
  "num_lanes": {
    "value": 4,
    "confidence": 0.88,
    "evidence": "Four lane markings visible ahead of ego vehicle."
  },
  "traffic_signals": {
    "present": true,
    "state": "red",
    "confidence": 0.91,
    "evidence": "Red signal clearly visible at top center of frame."
  }
}
```

처리 후 `confidence < 0.7` 인 필드를 별도로 수집합니다.

```python
# 위 예시에서 weather(0.55)가 low_confidence에 해당
low_confidence = {
    "weather": {"value": "clear", "confidence": 0.55, "evidence": "..."}
}
```

이 목록이 Stage 3으로 전달됩니다.

---

## Stage 3 — 자기 검증 (stage3_verify.py)

### 목적

Stage 2에서 모델이 확신하지 못했던 필드만 **다시 한번 영상을 보며 재확인**합니다.
모든 필드를 재검증하면 비용이 2배가 되므로, confidence < 0.7인 필드만 선별합니다.

### 비용 절감 효과

예를 들어 15개 필드 중 4개가 저확신이라면:
- Stage 3 없이 전체 재검증: 15개 필드 × 재검증 비용
- Stage 3 선별 재검증: **4개 필드만** → 약 73% 비용 절감

### 입력

- 영상 16프레임
- Stage 2의 저확신 필드 목록과 현재 값

### 프롬프트 예시

```
Watch this video again. Focus ONLY on these fields:
- weather: currently 'clear' (confidence 0.55) — evidence: no rain on lens but sky obscured

Verdict: CONFIRM (original is correct) or CORRECT (provide new value)?
```

### 응답 처리 로직

```
모델 응답
│
├─ verdict: "CONFIRM" → Stage 2 값 그대로 유지, verified=True 표시
│
└─ verdict: "CORRECT"
      │
      ├─ corrected_value로 기존 값 교체
      └─ confidence를 0.85로 상향 (재검증 완료 표시)
```

### 예시 응답

```json
{
  "weather": {
    "observation": "I can now see wet road surface reflections and droplets on the windshield.",
    "verdict": "CORRECT",
    "corrected_value": "rainy"
  }
}
```

Stage 3 결과가 최종 `verified_odd` 딕셔너리입니다.

---

## Stage 4 — 캡션 정제 (stage4_refine.py)

### 목적

Stage 1·2·3 결과를 모두 통합해 **정확하고 정보가 풍부한 최종 캡션**을 생성합니다.

### 입력

- 영상 16프레임
- 원본 캡션
- Stage 1: `hallucinated` (제거할 내용), `missed` (추가할 내용)
- Stage 3: `verified_odd` (검증된 ODD 정보 JSON)

### 프롬프트 구조

```
[원본 캡션]
  ↓ 이 내용을 삭제하세요:
[hallucinated 목록]
  ↓ 이 내용을 추가하세요:
[missed 목록]
  ↓ 이 정보를 자연스럽게 녹이세요:
[verified_odd JSON]

규칙:
- 150~300 단어
- 시간순 서술 (영상 시작 → 끝)
- 3인칭 과거시제 ("The ego-vehicle...")
- JSON이나 헤더 없이 텍스트만 출력
```

### 출력 예시

```
On a clear daytime morning, the ego-vehicle traveled along a four-lane urban road
in the rightmost lane. Moderate traffic flowed ahead, with several cars and one
bus maintaining steady speed. A traffic signal at the upcoming intersection turned
red, prompting the ego-vehicle to brake and come to a full stop behind queued
vehicles.

While stopped, a stalled car was visible on the left lane, partially obstructing
traffic flow. Two pedestrians approached the crosswalk and began crossing the
intersection from left to right. The ego-vehicle remained stationary, yielding
to the pedestrians. Once the signal returned to green and the crosswalk cleared,
the ego-vehicle resumed forward motion and proceeded through the intersection.
```

원본에서 hallucinated("Heavy rain was falling")가 제거되고,
missed("traffic signal turns red")와 verified_odd("clear weather", "4 lanes") 정보가 자연스럽게 통합됐습니다.

---

## API 안전장치 (이중 재시도)

네트워크 오류나 모델 응답 형식 오류에 대비해 두 층의 재시도 로직이 있습니다.

```
chat_json() 호출 (Stage 1·2·3)
│
├─ 내부 _chat() 호출
│     ├─ APIError / APITimeoutError 발생 시
│     │     → 지수 백오프: 2초, 4초, 8초 후 재시도
│     │     → 3회 실패 시 예외 전파
│     └─ 성공 시 응답 텍스트 반환
│
└─ _extract_json() 로 JSON 파싱 시도
      ├─ 성공 → 반환
      ├─ 실패 (모델이 설명 텍스트를 앞뒤에 붙인 경우)
      │     → _chat() 재호출 후 재파싱
      │     → 최대 3회
      └─ 3회 모두 실패 → 오류 로그 + 빈 결과 반환 (파이프라인은 계속)
```

**JSON 파싱 내성 처리:**

모델이 응답을 아래처럼 감쌀 때도 올바르게 파싱합니다.

```
Here is the JSON response:    ← 이 부분 무시
```json
{ "time_of_day": ... }
```                           ← 코드블록 제거 후 파싱
```

---

## 배치 처리 상세 (batch_runner.py)

### 동시성 모델

```python
sem = asyncio.Semaphore(2)    # 동시에 2개 클립만 처리

tasks = [create_task(process(clip)) for clip in 200_clips]
# 200개 Task를 한꺼번에 생성하지만
# Semaphore 때문에 실제 실행은 2개씩

for result in as_completed(tasks):
    # 완료되는 순서대로 수집
    # 완료 즉시 다음 대기 Task가 실행 시작
```

클립 하나당 API를 **최소 4회**(각 Stage 1회) 호출하므로, `concurrent=2` 는 vLLM 서버에 동시에 최대 8개의 요청이 들어갈 수 있음을 의미합니다.

### 진행 상태 추적

`progress.json` 구조:

```json
{
  "done":    ["clip_id_1", "clip_id_2", ...],
  "error":   ["clip_id_x"],
  "skipped": []
}
```

- **10개 처리마다** 저장 → 갑작스러운 종료 시 손실 최소화
- **재시작 시** `done` + `error` 에 있는 clip_id는 건너뜀
- `--reset` 플래그로 초기화 가능

### 진행 로그 예시

```
10:23:01 INFO batch_runner — Loaded 200 clip IDs from source=gap
10:23:01 INFO batch_runner — Total: 200  |  Already done: 47  |  Pending: 153
10:23:05 INFO pipeline    — [ef742bb7] Stage 1: grounding check
10:23:18 INFO pipeline    — [ef742bb7] Stage 2: ODD extraction
10:23:31 INFO pipeline    — [ef742bb7] Stage 3: self-verify (2 low-conf fields)
10:23:39 INFO pipeline    — [ef742bb7] Stage 4: caption refine
10:23:47 INFO pipeline    — [ef742bb7] Done — hal=1 missed=2 low_conf=2
10:24:27 INFO batch_runner — Progress: 10/153  ok=9 err=1  rate=14.2/min  ETA=10min
```

---

## 출력 파일 구조

### 1. 정제 캡션 (captions/{clip_id}.txt)

원본과 동일한 파일명 규칙을 사용하므로, 기존 파이프라인에 교체해서 사용할 수 있습니다.

### 2. 구조화 ODD (odd/{clip_id}.json)

```json
{
  "clip_id": "ef742bb7-c767-4848-a15b-7d39c565b45e",
  "odd_compat": {
    "time_of_day": "day",
    "weather": "rainy",
    "road_type": "intersection",
    "traffic_density": "moderate",
    "hazard_level": "medium",
    "agent_type": ["car", "bus", "pedestrian"],
    "ego_action": ["braking", "stopping"]
  },
  "odd_extended": {
    "time_of_day": {"value": "day", "confidence": 0.95, "evidence": "..."},
    "weather":     {"value": "rainy", "confidence": 0.85, "evidence": "...", "verified": true},
    "num_lanes":   {"value": 4, "confidence": 0.88, "evidence": "..."},
    "traffic_signals": {"present": true, "state": "red", "confidence": 0.91, "evidence": "..."}
  }
}
```

- `odd_compat`: 기존 `odd_tags.json` 스키마와 동일 → **현재 시스템에 바로 교체 가능**
- `odd_extended`: confidence·evidence 포함 완전 데이터 → **추후 품질 분석용**

### 3. 변경 내역 (diff/{clip_id}_diff.json)

```json
{
  "clip_id": "ef742bb7-c767-4848-a15b-7d39c565b45e",
  "grounded":    ["The ego-vehicle slows for a stalled car"],
  "hallucinated": ["Heavy rain was falling throughout"],
  "missed":      ["Traffic signal turns red", "Bus visible at bus stop"],
  "low_conf_fields": ["weather", "num_lanes"]
}
```

hallucinated 항목 수가 많은 클립을 사후 분석해 1차 캡션 생성 모델의 문제 유형을 파악하는 데 사용할 수 있습니다.

---

## 한 클립 처리 소요 시간 추정

| 단계 | 내용 | 소요 시간 (예상) |
|------|------|-----------------|
| 프레임 추출 | 16프레임 샘플링 + JPEG 인코딩 | ~0.5초 |
| Stage 1 | 영상 + 캡션 → hallucination 검출 | ~10~20초 |
| Stage 2 | 영상 → 15개 ODD 필드 추출 | ~15~25초 |
| Stage 3 | 저확신 필드 재검증 (평균 3~5개 필드) | ~8~15초 |
| Stage 4 | 정제 캡션 생성 | ~8~12초 |
| 파일 저장 | 3개 JSON/TXT 저장 | ~0.1초 |
| **합계** | | **~40~75초/클립** |

`concurrent=2` 기준 200개 처리 시 약 70~125분 예상.
`concurrent=4` 로 올리면 절반 수준으로 단축 가능합니다 (vLLM 서버 용량 확인 후 조정).
