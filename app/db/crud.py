"""CRUD operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Tenant, APIKey, UsageRecord
from datetime import datetime


async def get_tenant_by_email(db: AsyncSession, email: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.email == email))
    return result.scalar_one_or_none()


async def create_tenant(db: AsyncSession, name: str, email: str, hashed_password: str) -> Tenant:
    tenant = Tenant(name=name, email=email, hashed_password=hashed_password)
    db.add(tenant)
    await db.flush()
    return tenant


async def get_api_key_by_hash(db: AsyncSession, key_hash: str) -> APIKey | None:
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active))
    return result.scalar_one_or_none()


async def create_api_key(db: AsyncSession, tenant_id: int, key_hash: str, name: str) -> APIKey:
    api_key = APIKey(tenant_id=tenant_id, key_hash=key_hash, name=name)
    db.add(api_key)
    await db.flush()
    return api_key


async def create_usage_record(
    db: AsyncSession,
    tenant_id: int,
    api_key_id: int | None,
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    latency_ms: float,
    status: str,
) -> UsageRecord:
    record = UsageRecord(
        tenant_id=tenant_id,
        api_key_id=api_key_id,
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        cost=cost,
        latency_ms=latency_ms,
        status=status,
    )
    db.add(record)
    await db.flush()
    return record


async def get_tenant_usage(db: AsyncSession, tenant_id: int, days: int = 30) -> list[UsageRecord]:
    result = await db.execute(
        select(UsageRecord)
        .where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.created_at >= datetime.utcnow().replace(day=1)
        )
        .order_by(UsageRecord.created_at.desc())
    )
    return list(result.scalars().all())
