# Phase 1 소스 정찰 리포트 (recon.py)

블록별 게이트 — SUPPORTED=실데이터 지지 / LOW_RES=해상도 부족 /
HAND_ANCHOR=축 부재(§11 스윕) / INSUFFICIENT=컬럼 미검출 / NOT_OBTAINED=샘플 없음

| block | source | gate | achievable | missing | vocab / edge / note |
|---|---|---|---|---|---|
| P1_weather | KMA_ASOS | **SUPPORTED** | ['month', 'hour'] | - | - |
| P1_fog | KMA_ASOS | **SUPPORTED** | ['month', 'hour'] | - | - |
| w_vkt | KTDB | **SUPPORTED** | - | - | vocab=고속도로,일반도로; ⚠ 등급 커버 2/4 — 미확보 ['지방도', '국가지원지방도'] (itmsh_yearly 백엔드 미제공·502, 구조적 한계) |
| w_hourly | KTDB | **SUPPORTED** | ['road_type'] | - | vocab=고속도로,일반도로; edgeTV=0.0758; ⚠ 등급 커버 2/4 — 미확보 ['지방도', '국가지원지방도'] (itmsh_yearly 백엔드 미제공·502, 구조적 한계); edge grade→hour: TV=0.076 ≥ eps → 조건부 정당 |
| P4_speed | KTDB | **HAND_ANCHOR** | - | - | weather-dim |
| P3_agent | KoROAD | **HAND_ANCHOR** | - | - | 축 부재 → §11 민감도 스윕 |
| P3_density | KTDB | **HAND_ANCHOR** | - | - | V/C=용량편람(문서) 산출·API 부재 |
| P5_lighting | KASI | **HAND_ANCHOR** | - | - | brightness |

## 판정 요약
- SUPPORTED: ['P1_weather', 'P1_fog', 'w_vkt', 'w_hourly']
- ⚠ 등급 부분커버(SUPPORTED이나 모집단 일부 미확보·구조적 한계): ["w_vkt(미확보 ['지방도', '국가지원지방도'])", "w_hourly(미확보 ['지방도', '국가지원지방도'])"]
- 손앵커/저해상도(→§11 스윕·주의): ['P4_speed', 'P3_agent', 'P3_density', 'P5_lighting']
- 미확보/불충분(→샘플 확보·컬럼 확인): []

## 다음 조치
1. SUPPORTED 블록: sources/*.csv 실값 전사 → loader.py 계약 검증.
2. LOW_RES/HAND_ANCHOR: loader.BLOCKS 조건키 trim 또는 §11 민감도 스윕 대상 표기.
3. vocab_found로 mapping.yaml road_type taxonomy 확인(tunnel 부재 등).
4. edge TV < eps 블록: 해당 조건부 삭제(marginal) 검토.
