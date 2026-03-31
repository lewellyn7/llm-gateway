# LLM Gateway

> 企业级 OpenAI 兼容 API 网关 | Enterprise-grade OpenAI-compatible API Gateway

**语言:** [English](README.md) | [中文](README_CN.md)

---

## 特性

- 🌐 **多 Provider** - OpenAI、Claude、vLLM 等
- 🔄 **智能路由** - 支持成本、延迟、质量、均衡策略
- 📊 **多租户** - 租户管理、配额和 API Key
- 💰 **Token 计费** - 用量追踪和成本计算
- 🚦 **限流** - 基于 Redis 的滑动窗口限流
- 📝 **异步日志** - 基于 Kafka 的事件流
- 🔌 **OpenAI 兼容** - 完全兼容 OpenAI API
- 🛡️ **中间件** - 认证、用量追踪、请求追踪
- 🔧 **Tool Calling** - 可扩展的函数调用
- 📊 **管理后台** - Vue 3 + Tailwind CSS

## 快速开始

```bash
# 克隆
git clone https://github.com/lewellyn7/llm-gateway.git
cd llm-gateway

# 配置
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 启动
cd docker && docker-compose up -d

# 测试
curl http://localhost:28000/health
```

## API 使用

```bash
# Chat Completions
curl -X POST http://localhost:28000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'

# 列出模型
curl http://localhost:28000/v1/models \
  -H "Authorization: Bearer sk-your-key"

# Embeddings
curl -X POST http://localhost:28000/v1/embeddings \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "model": "text-embedding-3-small"}'
```

## 架构

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

## Provider 支持

| Provider | 模型 | 流式输出 |
|----------|------|---------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | ✅ |
| Claude | claude-3-5-sonnet, claude-3-opus | ✅ |
| vLLM | llama-3-70b, llama-3-8b, qwen-72b | ✅ |

## 路由策略

- **balanced** - 均衡成本和质量（默认）
- **cost** - 优先选择最低成本
- **latency** - 优先选择最低延迟
- **quality** - 优先选择最高质量

## Tool Calling

```bash
# 列出可用工具
curl http://localhost:28000/api/tools/list \
  -H "Authorization: Bearer sk-your-key"

# 调用工具
curl -X POST http://localhost:28000/api/tools/call \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"tool_calls": [{"name": "get_weather", "arguments": {"location": "Beijing"}}]}'
```

## 管理后台

访问 `/admin`（默认账号: admin/admin）

- 🏢 租户管理
- 🔑 API Key 生成
- 📊 用量统计
- ⚙️ 系统设置

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL 连接 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 连接 |
| `KAFKA_BOOTSTRAP_SERVERS` | localhost:9092 | Kafka brokers |
| `OPENAI_API_KEY` | - | OpenAI API Key |
| `ANTHROPIC_API_KEY` | - | Anthropic API Key |
| `VLLM_ENDPOINT` | - | vLLM 端点 |
| `SECRET_KEY` | change-me... | JWT 密钥 |

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 本地运行
uvicorn app.main:app --reload --port 8000
```

## Docker

```bash
# 构建
cd docker && docker build -t llm-gateway:latest .

# 运行
docker run -d -p 28000:8000 --env-file ../.env llm-gateway:latest
```

## Docker Compose

```bash
# 启动全部服务
cd docker && docker-compose up -d

# 查看日志
cd docker && docker-compose logs -f app

# 停止
docker-compose down
```

## CI/CD

GitHub Actions 流水线:
1. Lint (ruff)
2. Test (pytest)
3. Build (Docker)
4. Deploy (SSH)

## 项目结构

```
llm-gateway/
├── app/
│   ├── main.py           # FastAPI 应用
│   ├── core/            # 配置、安全、限流、日志
│   ├── api/             # API 路由
│   ├── services/        # 路由、计费、工具
│   ├── db/              # 会话、模型、CRUD
│   ├── middleware/      # 认证、用量、追踪
│   ├── schemas/         # Pydantic schemas
│   ├── providers/        # LLM 客户端
│   └── templates/        # 管理后台 UI
├── .github/workflows/    # CI/CD
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT
