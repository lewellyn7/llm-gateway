"""LLM Gateway - Main FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.kafka import kafka_producer
from app.core.limiter import rate_limiter
from app.middleware import AuthMiddleware, UsageMiddleware, TraceMiddleware

# API routes
from app.api.routes_llm import router as llm_router
from app.api.routes_claude import router as claude_router
from app.api.routes_tools import router as tools_router
from app.api.routes_media import router as media_router
from app.api.routes_embeddings import router as embeddings_router
from app.api.routes_admin import router as admin_router
from app.api.routes_oauth import router as oauth_router
from app.api.routes_telegram import router as telegram_router
from app.api.routes_telegram_admin import router as telegram_admin_router
from app.api.routes_discord import router as discord_router
from app.api.routes_rerank import router as rerank_router
from app.api.routes_slack import router as slack_router
from app.api.routes_logs import router as logs_router
from app.api.routes_billing_reports import router as billing_reports_router
from app.api.routes_websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    await kafka_producer.connect()
    await rate_limiter.connect()
    
    yield
    
    # Shutdown
    await kafka_producer.close()
    await rate_limiter.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TraceMiddleware)
app.add_middleware(UsageMiddleware)
app.add_middleware(AuthMiddleware)

# Routes - OAuth (before auth middleware)
app.include_router(oauth_router)

# Routes - Telegram
app.include_router(telegram_router)
app.include_router(telegram_admin_router)
app.include_router(discord_router)

# Routes - WebSocket
app.include_router(websocket_router)

# Routes - API
app.include_router(llm_router, prefix="/v1")
app.include_router(claude_router)
app.include_router(tools_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(embeddings_router, prefix="/v1")
app.include_router(rerank_router)
app.include_router(billing_reports_router)
app.include_router(slack_router)
app.include_router(logs_router)

# Routes - Admin
app.include_router(admin_router)


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "providers": {
            "openai": bool(settings.OPENAI_API_KEY),
            "claude": bool(settings.ANTHROPIC_API_KEY),
            "vllm": bool(settings.VLLM_ENDPOINT),
            "cohere": bool(settings.COHERE_API_KEY),
        },
        "oauth": {
            "github": bool(settings.GITHUB_CLIENT_ID),
            "google": bool(settings.GOOGLE_CLIENT_ID),
        },
        "websocket": {
            "enabled": True,
            "endpoint": "/ws/v1/chat/stream"
        }
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/capabilities")
async def capabilities():
    """Get gateway capabilities."""
    from app.services.llm_router import LLMRouter

    router = LLMRouter()
    return router.get_capabilities()
