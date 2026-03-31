"""
Kafka Producer for Async Logging
"""
import json
import asyncio
from datetime import datetime
from typing import Any
from aiokafka import AIOKafkaProducer
from app.core.config import settings


class KafkaProducer:
    """Async Kafka producer."""

    def __init__(self):
        self._producer: AIOKafkaProducer = None
        self._enabled: bool = True

    async def connect(self):
        """Connect to Kafka."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
        except Exception as e:
            print(f"Kafka connection failed: {e}. Continuing without Kafka.")
            self._enabled = False

    async def close(self):
        """Close Kafka connection."""
        if self._producer:
            await self._producer.stop()

    async def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
    ):
        """Send a message to a topic."""
        if not self._enabled or not self._producer:
            return

        try:
            await self._producer.send_and_wait(
                topic,
                value=value,
                key=key.encode("utf-8") if key else None,
            )
        except Exception as e:
            print(f"Kafka send failed: {e}")

    async def log_usage(
        self,
        tenant_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        status: str,
    ):
        """Log LLM usage event."""
        await self.send(
            settings.KAFKA_USAGE_TOPIC,
            {
                "event_type": "usage",
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "latency_ms": latency_ms,
                "status": status,
            },
            key=tenant_id,
        )

    async def log_request(
        self,
        tenant_id: str,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
    ):
        """Log API request."""
        await self.send(
            settings.KAFKA_LOG_TOPIC,
            {
                "event_type": "request",
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "latency_ms": latency_ms,
            },
            key=tenant_id,
        )

    async def log_billing_event(
        self,
        tenant_id: str,
        amount: float,
        currency: str,
        event_type: str,
    ):
        """Log billing event."""
        await self.send(
            settings.KAFKA_BILLING_TOPIC,
            {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_id,
                "amount": amount,
                "currency": currency,
            },
            key=tenant_id,
        )


kafka_producer = KafkaProducer()
