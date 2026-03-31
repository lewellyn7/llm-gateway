# Migration Guide: ai-gateway → llm-gateway

## Overview

**llm-gateway** is the redesigned successor to **ai-gateway**.

## Feature Comparison

| Feature | ai-gateway | llm-gateway |
|---------|------------|-------------|
| Architecture | g4f/LiteLLM | Multi-Provider Native |
| Database | SQLite | PostgreSQL + asyncpg |
| Rate Limiting | Middleware | Redis Sliding Window |
| Logging | Sync | Kafka Async |
| Multi-Tenant | Basic | Full (Tenant/Quota/APIKey) |
| Billing | None | Token-based |
| Streaming | Partial | Full SSE |
| Tool Calling | None | Extensible |
| Admin UI | Basic | Vue 3 Dashboard |
| CI/CD | Basic | Full GitHub Actions |
| API Compatibility | Partial | OpenAI Full |

## Migration Steps

### 1. Export Existing Data

From ai-gateway database:
- API keys and configurations
- Model pools
- Usage statistics

### 2. Deploy llm-gateway

```bash
cd llm-gateway

# Configure environment
cp .env.example .env
vim .env  # Add your API keys

# Start services
docker-compose up -d

# Check health
curl http://localhost:28000/health
```

### 3. Update Clients

Update API endpoint URLs:
```bash
# Old
https://your-old-gateway.com/v1/chat/completions

# New
https://your-new-gateway.com/v1/chat/completions
```

Update authentication headers (if using different key format):
```bash
# Same format
-H "Authorization: Bearer sk-your-key"
```

### 4. Verify

```bash
# Test chat completion
curl -X POST http://localhost:28000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "test"}]}'

# Check capabilities
curl http://localhost:28000/capabilities
```

## API Compatibility

### Compatible Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /v1/chat/completions` | ✅ | Full compatibility |
| `GET /v1/models` | ✅ | Full compatibility |
| `POST /v1/embeddings` | ✅ | Full compatibility |
| `POST /api/tools/call` | ✅ | New feature |
| `GET /api/tools/list` | ✅ | New feature |

### New Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /capabilities` | Gateway capabilities |
| `GET /health` | Enhanced health check |
| `/admin/*` | Admin dashboard |

### Removed Endpoints

| Old Endpoint | Replacement |
|-------------|-------------|
| `/api/pool/*` | Multi-tenant system |
| `/api/oauth/*` | Future feature |

## Rollback

If rollback needed, the old ai-gateway is preserved at:
```
/home/lewellyn/aigateway/ai-gateway/
```

## Support

- API Docs: `/docs`
- Health: `/health`
- Capabilities: `/capabilities`
