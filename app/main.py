"""LLM Gateway - Main FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.kafka import kafka_producer
from app.core.limiter import rate_limiter
from app.middleware import AuthMiddleware, UsageMiddleware, TraceMiddleware
from app.api.routes_llm import router as llm_router
from app.api.routes_claude import router as claude_router
from app.api.routes_tools import router as tools_router
from app.api.routes_media import router as media_router


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

# Routes
app.include_router(llm_router, prefix="/v1")
app.include_router(claude_router)
app.include_router(tools_router, prefix="/api")
app.include_router(media_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": "LLM Gateway API", "version": settings.APP_VERSION}
