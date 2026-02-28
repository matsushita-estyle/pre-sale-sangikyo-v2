"""FastAPI Hello World - Azure App Service B1"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.logging_config import setup_logging

# Setup logging
setup_logging(level="INFO")

app = FastAPI(
    title="Sangikyo V2 API",
    version="1.0.0",
    description="営業支援AIエージェント - バックエンドAPI",
)

# CORS設定（Next.jsからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では specific origins に変更
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (router already has prefix="/api/v1")
app.include_router(api_router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Hello World from FastAPI!",
        "service": "Sangikyo V2 Backend",
        "status": "running",
    }


@app.get("/api/health")
async def health():
    """ヘルスチェック"""
    return {"status": "healthy"}


@app.get("/api/hello")
async def hello(name: str = "World"):
    """Hello メッセージを返す（Next.jsから呼び出すテスト用）"""
    return {
        "message": f"Hello, {name}!",
        "from": "FastAPI Backend",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
