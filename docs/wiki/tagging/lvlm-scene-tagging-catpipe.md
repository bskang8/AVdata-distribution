# LVLM 기반 씬 자동 태깅 (CatPipe)

## 출처
- **저자**: Rivera, Lübberstedt, Uhlemann, Lienkamp (TU Munich)
- **연도**: 2025
- **학술대회**: WACV Workshop
- **GitHub**: https://github.com/TUMFTM/CatPipe
- **파일**: `literature/papers/rivera-2025-scenario-understanding-traffic-scenes.pdf`

---

## 핵심 아이디어

Large Visual Language Models(LVLMs)로 자율주행 씬을 **자동으로 분류·태깅**하는 파이프라인.  
재학습 없이 새로운 카테고리에 즉시 적용 가능 (zero-shot generalization).

### CatPipe 파이프라인

```
이미지 입력
    ↓
3단계 프롬프트 엔지니어링
    ↓
LVLM (GPT-4 / LLaVA 등)
    ↓
카테고리 태그 출력
```

### 3단계 프롬프트 (예: "시인성 저하" 태그)

1. **초기 프롬프트**: "Is visibility high or low in this scene, why?"
2. **키 용어 기반 정제**: 응답에서 핵심 판단 근거 추출
3. **최종 프롬프트**: "Question: Is the image too bright? Return only yes or no. Answer:"

### 16개 분류 카테고리

| 유형 | 카테고리 |
|------|---------|
| Detection | Person, Traffic sign, Traffic light, VRU count, Lane marks |
| Reasoning | Weather, Time of day, Land use, Road condition, Street config, Traffic scene, Road intersection, VIB, Number of lanes, Vehicle manoeuvre |

### 모델별 성능 비교 (평균 Accuracy / F1)

| 모델 | 특징 |
|------|------|
| GPT-4 Vision | Accuracy 75%, F1 낮음 (복잡 추론 우수) |
| LLaVA-1.6-34B | F1 가장 높음, 범용 |
| CogAgent (18B) | Traffic light 93.4% Accuracy |
| Composer-HD (8B) | Weather, VIB 분류 우수, 추론 14초로 느림 |
| LLaVA-1.5 (13B) | 가장 빠름 (0.42초), 전반 균형적 |

---

## 장단점

**장점**
- 재학습 없이 새 태그 추가 가능 (zero-shot)
- 기존 CNN 대비 F1 score에서 우위 (분포 불균형 시)
- 오픈소스 모델(LLaVA) 사용 가능 → 비용 통제 가능

**단점**
- Composer-HD: 단일 이미지 14초 → 83k 클립에 적용 시 약 322시간
- LLaVA-1.5: 빠르지만 복잡 추론 카테고리에서 정확도 낮음
- 연속 프레임 없이 단일 이미지 → temporal context 부족
- "Weather" 카테고리 F1 37% → 날씨 태그는 추가 검토 필요

---

## 프로젝트 적용 포인트

### Gap-3 (ODD 커버리지 36~62%) 핵심 해결책

현재 Regex 기반 태깅이 날씨/조도/도로유형을 놓치는 문제를 CatPipe LLaVA로 보완.

**실용적 구현:**
```python
from transformers import pipeline

# LLaVA-1.5 (13B): 빠른 추론, 균형적 성능
model = pipeline("visual-question-answering", model="llava-hf/llava-1.5-13b-hf")

# 각 클립의 키프레임 이미지에 대해
tags = {}
for category, prompt in catpipe_prompts.items():
    result = model(image=frame, question=prompt)
    tags[category] = result["answer"]
```

### 우선 적용 카테고리 (현재 Regex 미커버)
1. **Weather**: rainy, snowy, foggy, clear — F1 37% → LLM fallback 필요
2. **Time of day**: twilight, nighttime — Regex로 부분 커버
3. **Road condition**: wet, icy, snowy — 현재 전혀 미커버

### 비용-성능 트레이드오프
```
LLaVA-1.5 (13B): 0.42s/image × 83,000 clips = ~9.7시간 (GPU 1장)
LLaVA-1.6-34B: 1.5s/image × 83,000 clips = ~34시간
GPT-4 Vision: API 비용 ≈ $0.01/image × 83,000 ≈ $830
```

---

## 관련 갭

| 갭 | 연결 |
|----|------|
| Gap-3 | CatPipe가 "LLM fallback tagging" 구체적 구현 방법을 제시 |
| Gap-6 | 태그된 씬 카테고리로 쿼리 자동 생성 가능 |

## 관련 실험
- EXP-003 (Distribution Analysis): CatPipe 태그 결과를 UMAP과 연계
- 새 실험 후보 EXP-005: CatPipe 전체 파이프라인 적용 및 ODD 커버리지 재측정
