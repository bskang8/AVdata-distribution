# 실행 방법 (How to Run)

## 전제 조건

```bash
cd /Data1/home/bskang/AVdata-distirbution
source .venv/bin/activate
```

---

## 1. FastAPI 백엔드 (REST API)

```bash
uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000 --reload
```

| 엔드포인트 | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |

---

## 2. Streamlit UI (웹 페이지)

```bash
uv run streamlit run src/avdata/ui/app.py --server.port 8501
```

| 엔드포인트 | URL |
|---|---|
| Web UI | http://localhost:8501 |

> **Tip:** `transformers` 라이브러리의 불필요한 모듈 스캔으로 인한 `ModuleNotFoundError` 로그 노이즈를 없애려면 `--server.fileWatcherType none` 옵션을 추가합니다.

```bash
uv run streamlit run src/avdata/ui/app.py --server.port 8501 --server.fileWatcherType none
```

---

## 동시 실행 (권장 순서)

> FastAPI를 먼저 실행한 뒤 Streamlit을 실행합니다.

**터미널 1 — API 서버:**
```bash
uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**터미널 2 — Streamlit UI:**
```bash
uv run streamlit run src/avdata/ui/app.py --server.port 8501 --server.fileWatcherType none
```

---

## nohup 백그라운드 실행

터미널을 닫아도 서버가 유지되어야 할 때 사용합니다.

**API 서버:**
```bash
nohup uv run uvicorn avdata.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
echo "API PID: $!"
```

**Streamlit UI:**
```bash
nohup uv run streamlit run src/avdata/ui/app.py \
  --server.port 8501 \
  --server.fileWatcherType none \
  --server.headless true \
  > logs/streamlit.log 2>&1 &
echo "Streamlit PID: $!"
```

> 로그 디렉토리가 없다면 먼저 생성: `mkdir -p logs`

**프로세스 종료:**
```bash
# PID로 종료
kill <PID>

# 포트로 찾아서 종료
kill $(lsof -ti :8000)   # API
kill $(lsof -ti :8501)   # Streamlit
```
