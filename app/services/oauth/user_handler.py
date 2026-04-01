"""OAuth user handler - auto register/login users."""

from app.db.session import AsyncSessionLocal
from app.db.models import Tenant, APIKey, Quota
from app.core.security import generate_api_key, hash_api_key
from datetime import datetime, timezone, timedelta


class OAuthUserHandler:
    """Handle OAuth user creation and login."""

    @staticmethod
    async def get_or_create_user(
        provider: str, provider_id: str, email: str, name: str
    ) -> dict:
        """
        Get existing user or create new one from OAuth.

        Returns dict with user info and API key.
        """
        async with AsyncSessionLocal() as db:
            # Check if tenant exists by email
            from sqlalchemy import select

            stmt = select(Tenant).where(Tenant.email == email)
            result = await db.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                # Create new tenant
                tenant = Tenant(
                    name=name or email.split("@")[0],
                    email=email,
                    plan="pro",  # OAuth users get Pro by default
                    is_active=True,
                )
                db.add(tenant)
                await db.flush()

                # Create API key for new user
                api_key = generate_api_key()
                key_hash = hash_api_key(api_key)
                api_key_record = APIKey(
                    tenant_id=tenant.id,
                    key_hash=key_hash,
                    key_prefix=api_key[:12],
                    name=f"{provider.title()} OAuth",
                    is_active=True,
                )
                db.add(api_key_record)

                # Create quota
                quota = Quota(
                    tenant_id=tenant.id,
                    monthly_limit=100000,  # Pro plan
                    used=0,
                    reset_at=datetime.now(timezone.utc) + timedelta(days=30),
                )
                db.add(quota)
                await db.commit()

                return {
                    "tenant": {
                        "id": tenant.id,
                        "name": tenant.name,
                        "email": tenant.email,
                        "plan": tenant.plan,
                    },
                    "api_key": api_key,
                    "is_new_user": True,
                }

            # Existing user - check if they have an API key
            stmt = select(APIKey).where(APIKey.tenant_id == tenant.id, APIKey.is_active)
            result = await db.execute(stmt)
            api_key_record = result.scalar_one_or_none()

            if not api_key_record:
                # Create API key if none exists
                api_key = generate_api_key()
                key_hash = hash_api_key(api_key)
                api_key_record = APIKey(
                    tenant_id=tenant.id,
                    key_hash=key_hash,
                    key_prefix=api_key[:12],
                    name=f"{provider.title()} OAuth",
                    is_active=True,
                )
                db.add(api_key_record)
                await db.commit()
            else:
                api_key = None  # Don't expose existing key

            return {
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "email": tenant.email,
                    "plan": tenant.plan,
                },
                "api_key": api_key,
                "is_new_user": False,
            }
