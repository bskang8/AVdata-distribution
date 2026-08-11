"""exposure 파이프라인 공용 경로 — 모든 스크립트가 여기서 디렉토리를 얻는다.

파일마다 반복되던 `HERE = os.path.dirname(...)` 보일러플레이트와 phase0 `../../` sys.path
부트스트랩을 한 곳으로 흡수한다. 이 파일이 **exposure/ 루트**에 있다는 전제로 절대경로 계산.

- root 스크립트(loader·compose·criticality·run_all): `import paths` 바로 됨(같은 폴더).
- 서브디렉토리 스크립트(procure/·select/): 상단에 root를 sys.path에 한 줄 추가 후 import:
      import os, sys
      sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
      import paths
  그러면 `import loader/compose/criticality`(root 공유코어)도 그대로 된다.
- import 시 phase0(step_a_odd_coverage·config)를 sys.path에 얹어준다 → pself·criticality가
  crosswalk 원시함수를 그대로 import(phase0 무수정).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))              # .../phase0_2/exposure
RAW = os.path.join(ROOT, "raw")
SOURCES = os.path.join(ROOT, "sources")
RECON = os.path.join(ROOT, "recon")
OUTPUT = os.path.join(ROOT, "output")
PHASE0 = os.path.abspath(os.path.join(ROOT, "..", "..", "phase0"))

# phase0 crosswalk(step_a_odd_coverage·config) import 가능하게 — pself·criticality 재사용
if PHASE0 not in sys.path:
    sys.path.insert(0, PHASE0)
