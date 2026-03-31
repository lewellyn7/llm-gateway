# LLM Gateway

> Enterprise-grade OpenAI-compatible API Gateway with Multi-Provider Support

**Language:** [English](README.md) | [中文](README_CN.md)

---

## Features

- 🌐 **Multi-Provider** - OpenAI, Claude, vLLM, and more
- 🔄 **Smart Routing** - Cost, latency, quality, or balanced strategies
- 📊 **Multi-Tenant** - Tenant management with quotas and API keys
- 💰 **Token Billing** - Usage tracking and cost calculation
- 🚦 **Rate Limiting** - Redis-based sliding window limiter
- 📝 **Async Logging** - Kafka-based event streaming
- 🔌 **OpenAI Compatible** - Drop-in replacement for OpenAI API
- 🛡️ **Middleware** - Auth, usage tracking, request tracing
- 🔧 **Tool Calling** - Extensible function calling
- 📊 **Admin Dashboard** - Vue 3 + Tailwind CSS

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

# Embeddings
curl -X POST http://localhost:28000/v1/embeddings \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "model": "text-embedding-3-small"}'
```

## Architecture

```
┌───────────────┐
│   Clients     │
└───────┬───────┘
        ↓
┌───────────────────┐
│  API Gateway      │
│  (FastAPI)        │
└────┬────────┬─────┘
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

## Providers

| Provider | Models | Streaming |
|----------|--------|-----------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | ✅ |
| Claude | claude-3-5-sonnet, claude-3-opus | ✅ |
| vLLM | llama-3-70b, llama-3-8b, qwen-72b | ✅ |

## Routing Strategies

- **balanced** - Balance cost and quality (default)
- **cost** - Prefer cheapest provider
- **latency** - Prefer fastest provider
- **quality** - Prefer best quality provider

## Tool Calling

```bash
# List available tools
curl http://localhost:28000/api/tools/list \
  -H "Authorization: Bearer sk-your-key"

# Call tools
curl -X POST http://localhost:28000/api/tools/call \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"tool_calls": [{"name": "get_weather", "arguments": {"location": "Beijing"}}]}'
```

## Admin Dashboard

Access at `/admin` (default: admin/admin)

- 🏢 Tenant management
- 🔑 API key generation
- 📊 Usage statistics
- ⚙️ System settings

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL connection |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:9092 | Kafka brokers |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `VLLM_ENDPOINT` | - | vLLM endpoint |
| `SECRET_KEY` | change-me... | JWT secret |

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run locally
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# Build
docker build -t llm-gateway:latest .

# Run
docker run -d -p 28000:8000 --env-file .env llm-gateway:latest
```

## Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## CI/CD

GitHub Actions pipeline:
1. Lint (ruff)
2. Test (pytest)
3. Build (Docker)
4. Deploy (SSH)

## Project Structure

```
llm-gateway/
├── app/
│   ├── main.py           # FastAPI app
│   ├── core/            # Config, security, limiter, logging
│   ├── api/             # API routes
│   ├── services/        # Router, billing, tools
│   ├── db/              # Session, models, crud
│   ├── middleware/      # Auth, usage, trace
│   ├── schemas/         # Pydantic schemas
│   ├── providers/        # LLM clients
│   └── templates/        # Admin UI
├── .github/workflows/    # CI/CD
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT
