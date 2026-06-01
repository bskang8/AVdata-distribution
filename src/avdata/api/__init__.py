"""Run with: uv run python -m avdata.api"""
import uvicorn


def main():
    uvicorn.run(
        "avdata.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
