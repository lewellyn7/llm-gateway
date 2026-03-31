# LLM Gateway

> Enterprise-grade OpenAI-compatible API Gateway with Multi-Provider Support

## Features

- 🌐 **Multi-Provider** - OpenAI, Claude, vLLM, and more
- 🔄 **Smart Routing** - Cost, latency, quality, or balanced strategies
- 📊 **Multi-Tenant** - Tenant management with quotas and API keys
- 💰 **Token Billing** - Usage tracking and cost calculation
- 🚦 **Rate Limiting** - Redis-based sliding window limiter
- 📝 **Async Logging** - Kafka-based event streaming
- 🔌 **OpenAI Compatible** - Drop-in replacement for OpenAI API
- 🛡️ **Middleware** - Auth, usage tracking, request tracing

## Quick Start

```bash
# Clone
git clone https://github.com/lewellyn7/llm-gateway.git
cd llm-gateway

# Configure
cp .env.example .env
# Edit .env with your API keys

# Start
docker-compose up -d

# Test
curl http://localhost:28000/health
```

## API Usage

```bash
# Chat Completions
curl -X POST http://localhost:28000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'

# List Models
curl http://localhost:28000/v1/models \
  -H "Authorization: Bearer sk-your-key"
```

## Architecture

```
┌───────────────┐
│   Clients     │
└───────┬───────┘
        ↓
┌───────────────────┐
│  API Gateway      │
│  (FastAPI)       │
└────┬────────┬────┘
     ↓        ↓
┌─────────┐ ┌──────────────┐
│ Auth    │ │ Router       │
│ Middleware│ │ Engine       │
└────┬────┘ └──────┬───────┘
     ↓        ↓
┌─────────────┐ ┌─────────────────┐
│ PostgreSQL │ │ LLM Providers   │
│ Redis     │ │ OpenAI/Claude  │
│ Kafka     │ │ vLLM           │
└─────────────┘ └─────────────────┘
```

## Documentation

- [Migration Guide](MIGRATION.md) - From ai-gateway
- [API Reference](#api-endpoints)
- [Configuration](#environment-variables)

## License

MIT
