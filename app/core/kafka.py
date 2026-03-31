"""Kafka producer for async logging."""
import json
from datetime import datetime
from aiokafka import AIOKafkaProducer
from app.core.config import settings


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer = None
        self._enabled: bool = True

    async def connect(self):
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
        except Exception as e:
            print(f"Kafka connection failed: {e}")
            self._enabled = False

    async def close(self):
        if self._producer:
            await self._producer.stop()

    async def send(self, topic: str, value: dict, key: str | None = None):
        if not self._enabled or not self._producer:
            return
        try:
            await self._producer.send_and_wait(
                topic, value=value,
                key=key.encode() if key else None,
            )
        except Exception as e:
            print(f"Kafka send failed: {e}")

    async def log_usage(self, tenant_id, model, prompt_tokens, completion_tokens, latency_ms, status):
        await self.send(settings.KAFKA_USAGE_TOPIC, {
            "event_type": "usage",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "status": status,
        }, key=tenant_id)

    async def log_request(self, tenant_id, method, path, status_code, latency_ms):
        await self.send(settings.KAFKA_LOG_TOPIC, {
            "event_type": "request",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
        }, key=tenant_id)


kafka_producer = KafkaProducer()
