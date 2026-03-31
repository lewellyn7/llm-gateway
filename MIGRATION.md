# Migration Guide: ai-gateway → llm-gateway

## Overview

**llm-gateway** is the redesigned successor to **ai-gateway**.

## Comparison

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
| API Compatibility | Partial | OpenAI Full |

## Key Changes

### 1. Configuration
```bash
# Old: .env file
# New: .env + docker-compose.yml
```

### 2. Database
```bash
# Old: SQLite file
# New: PostgreSQL with asyncpg
```

### 3. API Keys
```bash
# Old: Simple keys
# New: Tenant-bound keys with quotas
```

### 4. Environment Variables

| Old | New |
|-----|-----|
| `ADMIN_USER` | `POSTGRES_USER` |
| `ADMIN_PASSWORD` | `POSTGRES_PASSWORD` |
| `DB_TYPE` | `DATABASE_URL` |
| - | `REDIS_URL` |
| - | `KAFKA_BOOTSTRAP_SERVERS` |
| - | `OPENAI_API_KEY` |
| - | `ANTHROPIC_API_KEY` |
| - | `VLLM_ENDPOINT` |

## Migration Steps

### 1. Export Existing Data
```bash
# Export API keys from ai-gateway
# Export model configurations
```

### 2. Deploy llm-gateway
```bash
cd llm-gateway
docker-compose up -d
```

### 3. Import Data
```bash
# Import API keys
# Import model configurations
```

### 4. Update Clients
```bash
# Update API endpoint URLs
# Update authentication headers
```

## API Compatibility

### Compatible
- `POST /v1/chat/completions` ✅
- `GET /v1/models` ✅
- `POST /v1/embeddings` ✅

### New Endpoints
- `GET /capabilities` - Gateway capabilities
- `GET /health` - Enhanced health check
- `/api/tools/*` - Tool calling
- `/api/media/*` - Multimodal

### Removed
- `/api/pool/*` - Pool management (replaced by multi-tenant)
- `/api/oauth/*` - OAuth (future feature)
- `/admin/*` - Admin UI (new UI coming)

## Environment Setup

```bash
# Copy example env
cp .env.example .env

# Edit with your values
vim .env

# Start services
docker-compose up -d
```

## Rollback

If rollback needed, the old ai-gateway is preserved at:
```
/home/lewellyn/aigateway/ai-gateway/
```

## Support

For issues or questions, check:
- `/docs` - API documentation
- `/capabilities` - Gateway capabilities
- `/health` - Health check with provider status
