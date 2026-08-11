# phase2 데이터 근거 — 왜 nuScenes인가, 캡션/임베딩은 필요한가

> 워킹 분석 문서(재분석용). 방향 권위 문서는 `../PAPER_DIRECTION.md`(§5-1 feature 정의), 실행은 `README.md`·`../EXECUTION_PLAN.md`.
> 확정되면 요지는 PAPER_DIRECTION §5-1로 승격. 작성 2026-08-11.

## 발단 (질문)
"이전 실험은 캡셔닝 데이터+임베딩 벡터를 썼는데, nuScenes엔 그런 자료가 없다. 그런데도 실험이 온전히 되나?"

---

## 1. 파일럿 vs 실타깃 — 층위가 다르다

| | 이전(phase1) | 지금(phase2) |
|---|---|---|
| 성격 | **egomotion 써로게이트 파일럿** | **실 E2E 실타깃** |
| 데이터 | 83k 캡셔닝 클립 + 임베딩 | nuScenes |
| 모델 | 얕은 써로게이트(egomotion ADE/FDE) | SparseDrive-S (실 E2E, L2/collision) |
| 근거 강도 | 약함(feature-임계 자명성·n=10~15) | 논문 근거 |
| 역할 | **설계 자산** 제공(estimator·leave-out·"예측불가≠회복가능") | thesis 검정(크로스-아키텍처 전이·headroom) |

- Paper C thesis = **"실 E2E 주행에서 회복가치가 여러 아키텍처로 재사용되는가"**(`V=V_intrinsic+V_model` 분해).
- 이걸 재려면 (i) 실 E2E 모델, (ii) closed-loop/L2·collision **안전-치명 tail 지표**(PAPER_DIRECTION §5-4), (iii) 경쟁자(MOSAIC·RoCA·ActiveAD)가 겨루는 **표준 벤치마크**(§9)가 필요 → **nuScenes+SparseDrive**. 83k 캡션 데이터로는 이 셋을 못 만든다.
- 설계 원칙: 파일럿의 효과크기·라벨요구량은 **상속 금지, 실타깃서 재측정**(§4, G0~G3).

---

## 2. R0는 캡션/임베딩을 전혀 쓰지 않는다

지금 돌리는 R0(`r0_repro/`)는 **방법론이 아니라 재현·디리스킹**(README §R0 체크리스트):
1. SparseDrive-S 재현 → baseline L2/collision
2. stage1/stage2 시간·메모리 실측
3. **stage2-only leave-out 프로토타입**(결핍 제거→되메움 재학습이 값싸게 되나)

→ estimator·캡션·임베딩 **미등장**. 필요 입력 = nuScenes 이미지/주석/can_bus/맵뿐(전부 확보됨). **R0는 캡션 무관하게 100% 온전.**

---

## 3. 방법론 단계(R1+)에서도 캡션은 "필수 전제"가 아니다

estimator 입력은 **backbone-free model-agnostic 소스만**(PAPER_DIRECTION §5-1, thesis의 급소). 그 후보 대부분이 **nuScenes 네이티브**:

| feature | nuScenes 출처 | 상태 |
|---|---|---|
| ego kinematics(속도·가감속·yaw·곡률) | can_bus / ego_pose | ✅ 있음 |
| HD맵·도로 위상 | map expansion | ✅ 있음 |
| 에이전트 배치 메타(수·상대속도) | sample_annotation | ✅ 있음 |
| ODD 라벨 | 씬 메타 파생 | ✅ 파생 |
| **씬 캡션 임베딩** | 6-cam에 동일 캡셔닝 파이프라인 재실행해 생성 | ⏳ **선택·재생성** |

- 캡션 임베딩 = §5-1 후보 중 **하나이자 선택적**. nuScenes가 "결손"인 게 아니라, 83k엔 이미 붙어있었을 뿐 — 필요하면 동일 파이프라인으로 만들면 됨.
- **결핍 정의도 바뀜**: 파일럿의 feature-임계 클러스터 → **planning-relevant 실패 클러스터**(급코너·비보호좌회전·인터랙션·occlusion), nuScenes 씬 구조/안전지표로 정의(§5-1·§8). 캡션 아님.

---

## 4. 정직한 caveat (남는 실작업)
- R0: 캡션 무관, 온전. ✅
- R1+: nuScenes 위에 (a) 결핍 클러스터 **신규 정의**, (b) 캡션을 feature로 쓸 거면 nuScenes에 **재생성** — 예정된 절차(버그 아님, §4·G0~G3).

**한 줄**: 캡션/임베딩은 nuScenes의 결손이 아니라, 지금(R0)은 불필요하고 나중엔 필요하면 만들어 붙이는 **선택적 feature**.

---

## 5. 열린 질문 / 재분석 TODO
- [ ] 캡션 임베딩이 §5-1 네이티브 feature(kinematics·맵·에이전트) 대비 **한계이득**이 있나? (재생성 비용 정당화 검증 — 없으면 캡션 생략)
- [ ] nuScenes 안전-치명 tail이 **고여지(G0)**인가? 저여지면 학습 신호 불필요 → 캡션이든 뭐든 estimator 자체가 불요.
- [ ] 결핍 클러스터를 어떤 메타로 정의? (급코너=곡률 임계 / 인터랙션=에이전트 상대속도 / occlusion=? ) — nuScenes 파생 가능성 점검.
- [ ] 파일럿 83k의 캡션 스키마 ↔ nuScenes 6-cam 캡션 스키마 정합(재사용 시).
- [ ] backbone-free 강제 확인: estimator가 SparseDrive 지각 feature를 실수로 흡수하지 않도록 feature 출처 화이트리스트.
