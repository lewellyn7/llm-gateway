"""Database initialization."""
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.models import Base
from app.core.config import settings


async def init_db():
    """Create all database tables."""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
