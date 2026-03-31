"""Structured logging with Kafka."""

import json
from datetime import datetime
from app.core.kafka import kafka_producer


class Logger:
    """Structured logger with Kafka backend."""

    async def log(self, level: str, message: str, **kwargs):
        """Log a structured message."""
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        await kafka_producer.log_request(
            tenant_id=kwargs.get("tenant_id", "system"),
            method=kwargs.get("method", ""),
            path=kwargs.get("path", ""),
            status_code=kwargs.get("status_code", 200),
            latency_ms=kwargs.get("latency_ms", 0),
        )
        print(json.dumps(data))

    async def info(self, message: str, **kwargs):
        await self.log("INFO", message, **kwargs)

    async def error(self, message: str, **kwargs):
        await self.log("ERROR", message, **kwargs)

    async def warning(self, message: str, **kwargs):
        await self.log("WARNING", message, **kwargs)


logger = Logger()
