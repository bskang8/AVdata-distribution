# S1 캠페인 크래시 복구 런북

재부팅/멈춤으로 학습이 죽었을 때 이 순서대로. (근거: 2026-08-12 진단)

## 0. 증상
- `bash r0_repro/s1_status.sh`가 arm을 "진행중"으로 보여주는데 로그 tail이 한 지점에 멈춰있음.
- 실제로는 러너·train 프로세스 없음: `pgrep -af s1_campaign.sh` / `nvidia-smi` idle.

## 1. 언제·왜 죽었나 확인
```bash
last -x reboot | head            # 부팅 시각 = 로그 끊긴 시각이면 재부팅으로 죽은 것
journalctl -b -1 | tail          # 종료 직전 로그. systemd "Stopping/Unmounting" 없이 뚝 끊김 = 하드 크래시(정상 재부팅 아님)
sudo grep -iE "panic|oops|mce|thermal|throttl|xid|nvrm|hardware error" /var/log/kern.log /var/log/kern.log.1
```
해석:
- **thermal/throttl** → 냉각. (참고: 4090 스로틀 ~83°C. idle 35~41°C였음 = 열 아님.)
- **mce / hardware error / voltage** → CPU·메모리·전원.
- **panic/oops/xid** → 소프트웨어·GPU 드라이버.
- **크래시 직전 몇 분간 커널 로그가 통째로 없고 그냥 끊김** → 전원 즉사(PSU OCP/순간정전). ← 2026-08-12이 이 케이스.

## 2. 근본 원인 (2026-08-12 결론)
컨슈머 B760 보드 + 4090 2장 단일 PSU. **GPU 피크 전력 스파이크가 PSU 보호(OCP) 트립 → 즉시 차단.**
- 2-GPU 학습 시작 ~4분 만에 즉사. 열·패닉·Xid 로그 전무 = 전원 계열.
- 타 사용자(bjkang) Carla가 같은 박스 GPU에서 동시에 돌면 **합산 전력**으로 위험 가중.
- 소프트웨어로 "고치는" 문제 아님 → 아래로 부하·스파이크를 낮춰서 회피.

## 3. 재개 전 상태 정리
```bash
cd experiments/EXP-003/phase2
rm -rf r0_repro/output/s1_claims                 # 죽은 러너의 유령 claim 제거(안 하면 미완 arm이 막힘)
ls r1_gates/output_val/tail_*.json               # 완료 arm(skip 대상) 확인
nvidia-smi                                        # 타 사용자 점유·여유메모리·전력 확인
```

## 4. 전력 스파이크 억제 (핵심 방어, sudo 필요)
```bash
sudo nvidia-smi -pm 1
sudo nvidia-smi -pl 300          # 450→300W. 학습 성능 ~90% 유지, 위험 스파이크 제거. 두 GPU 다 적용.
# GPU1만: sudo nvidia-smi -i 1 -pl 300
```
- 돌아가는 중에 걸어도 즉시 적용됨.
- 두 GPU 캡은 타 사용자 Carla도 스로틀 → 한마디 해두면 예의.

## 5. 재개 (부하 최소화 = 단일 GPU 우선)
```bash
# 비어있는 GPU 하나로만. 타 사용자와 GPU가 안 겹치게 인덱스 선택.
setsid bash r0_repro/s1_campaign.sh 1 > r0_repro/output/campaign_gpu1.log 2>&1 &
# 안정 확인되면(수 시간 무크래시) 다른 GPU도 추가:
# setsid bash r0_repro/s1_campaign.sh 0 > r0_repro/output/campaign_gpu0.log 2>&1 &
```
- 완료 arm은 skip, 부분학습 arm은 `latest.pth`부터 자동 재개.
- **체크포인트 간격은 이미 500 iter(≈4분)로 축소됨** (`s1_leaveout_stage2.py`, env `S1_CKPT_INTERVAL`로 조정). 크래시해도 손실 ≤4분.

## 6. 진행 확인
```bash
bash r0_repro/s1_status.sh
```

---
### 판단 기준 요약
- GPU 비었나 + 타 사용자 없나 → 있으면 합산 전력 위험, 겹치지 않는 GPU 선택 or 조율.
- 재개는 **1-GPU + 전력캡 300W + 촘촘한 체크포인트**로 시작 → 안정 확인 후 2-GPU 확장.
- 또 즉사 + 전원 로그 무흔적 반복 → 소프트로 끝. **PSU 용량/전원 물리 점검** 필요.
