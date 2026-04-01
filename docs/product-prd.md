# LLM Gateway 产品PRD

> 版本：v1.0 | 状态：评审中 | 作者：Jarvis | 更新：2026-04-01

---

## 一、产品概述

### 1.1 产品定位

LLM Gateway 是一个**企业级 OpenAI 兼容 API 网关**，为开发者提供统一的 LLM 调用入口，支持多 Provider 接入、智能路由、多租户管理和计费功能。

### 1.2 核心价值

| 价值 | 说明 |
|------|------|
| **统一入口** | 一个 API 接口访问多个 LLM 提供商 |
| **成本优化** | 智能路由选择最优 Provider，降低成本 |
| **多租户** | 支持多租户隔离，配额管理和计费 |
| **OpenAI 兼容** | 无缝迁移现有 OpenAI 应用 |

---

## 二、功能架构

### 2.1 功能矩阵

| 一级模块 | 二级功能 | 优先级 | 状态 | 备注 |
|----------|----------|--------|------|------|
| **API 能力** | | | | |
| | Chat Completions | P0 | ✅ | OpenAI 兼容 |
| | Completions | P1 | 🔄 | 进行中 |
| | Embeddings | P0 | ✅ | |
| | Models List | P0 | ✅ | |
| | Tool Calling | P1 | ✅ | |
| | Streaming | P0 | ✅ | SSE 支持 |
| **Provider 接入** | | | | |
| | OpenAI | P0 | ✅ | |
| | Anthropic Claude | P0 | ✅ | |
| | vLLM | P1 | ✅ | |
| | Azure OpenAI | P2 | ❌ | 待接入 |
| **智能路由** | | | | |
| | Router Engine | P0 | ✅ | |
| | Cost 策略 | P0 | ✅ | |
| | Latency 策略 | P0 | ✅ | |
| | Quality 策略 | P0 | ✅ | |
| | Balanced 策略 | P0 | ✅ | |
| **多租户** | | | | |
| | 租户管理 | P0 | ✅ | CRUD |
| | API Key 管理 | P0 | ✅ | 生成/撤销 |
| | 配额管理 | P1 | ❌ | 待实现 |
| | 配额限制 | P1 | ❌ | 待实现 |
| **计费系统** | | | | |
| | Token 计费 | P0 | ✅ | |
| | 用量记录 | P0 | ✅ | |
| | 成本统计 | P1 | 🔄 | 部分完成 |
| | 计费报表 | P2 | ❌ | 待实现 |
| **中间件** | | | | |
| | 认证中间件 | P0 | ✅ | API Key |
| | 用量追踪 | P0 | ✅ | |
| | 请求追踪 | P0 | ✅ | Trace ID |
| | 限流 | P0 | ✅ | Redis |
| **异步日志** | | | | |
| | Kafka Producer | P1 | ✅ | |
| | 用量日志 | P1 | ✅ | |
| | 请求日志 | P1 | ✅ | |
| | 计费事件 | P1 | 🔄 | 部分完成 |
| **管理后台** | | | | |
| | Admin UI | P0 | ✅ | Vue SPA |
| | 租户管理 | P0 | ✅ | |
| | API Key 管理 | P0 | ✅ | |
| | 用量统计 | P1 | 🔄 | JSON 展示 |
| | 系统设置 | P2 | 🔄 | |
| **OAuth 认证** | | | | |
| | GitHub OAuth | P1 | ✅ | |
| | Google OAuth | P1 | ✅ | |
| | JWT Token | P0 | ✅ | |
| **DevOps** | | | | |
| | Docker 部署 | P0 | ✅ | |
| | Docker Compose | P0 | ✅ | |
| | CI/CD | P0 | ✅ | GitHub Actions |
| | 多阶段构建 | P0 | ✅ | |

---

## 三、API 规格

### 3.1 核心接口

#### 3.1.1 Chat Completions

```bash
POST /v1/chat/completions
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "model": "gpt-4o",          # required
  "messages": [                # required
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,          # optional, default 0.7
  "max_tokens": 1000,          # optional
  "stream": false,             # optional, default false
  "tools": [...]              # optional, for tool calling
}
```

**响应（non-streaming）**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "gpt-4o",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  }
}
```

#### 3.1.2 Embeddings

```bash
POST /v1/embeddings
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "model": "text-embedding-3-small",
  "input": "The quick brown fox jumps over the lazy dog"
}
```

#### 3.1.3 Models List

```bash
GET /v1/models
Authorization: Bearer {api_key}
```

---

## 四、数据模型

### 4.1 数据库 Schema

| 表 | 字段 | 说明 |
|----|------|------|
| **tenants** | id, name, email, plan, is_active, created_at | 租户表 |
| **api_keys** | id, tenant_id, key_hash, key_prefix, name, is_active, created_at, expires_at | API Key 表 |
| **usage_records** | id, tenant_id, model, provider, prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, status, created_at | 用量记录 |
| **quotas** | id, tenant_id, monthly_limit, used, reset_at | 配额表 |

### 4.2 Redis Keys

| Key Pattern | 说明 | TTL |
|-------------|------|-----|
| `rate:{api_key}` | 限流计数器 | 60s |
| `quota:{tenant_id}` | 配额计数器 | 30d |

---

## 五、路由策略

### 5.1 策略类型

| 策略 | 逻辑 | 适用场景 |
|------|------|----------|
| **cost** | 选择成本最低的 Provider | 成本敏感 |
| **latency** | 选择响应最快的 Provider | 实时交互 |
| **quality** | 选择最高质量模型 | 高质量输出 |
| **balanced** | 综合成本和质量（默认） | 通用场景 |

### 5.2 模型映射

| 模型 | Provider | 单价($/1M tokens) |
|------|----------|-------------------|
| gpt-4o | OpenAI | input: $5, output: $15 |
| gpt-4o-mini | OpenAI | input: $0.15, output: $0.60 |
| claude-3-5-sonnet | Anthropic | input: $3, output: $15 |
| llama-3-70b | vLLM | input: $0, output: $0 |

---

## 六、计费规则

### 6.1 计算公式

```
总成本 = Σ(prompt_tokens × 单价_in + completion_tokens × 单价_out)
```

### 6.2 计费周期

- **月度结算**：每月 1 日重置配额
- **按量付费**：超出配额按单价计费

---

## 七、安全规格

### 7.1 认证方式

| 方式 | 说明 |
|------|------|
| API Key | `Authorization: Bearer {key}` |
| OAuth | GitHub / Google 登录 |

### 7.2 限流规则

| 计划 | QPS | 分钟限额 | 日限额 | 月限额 |
|------|-----|---------|-------|-------|
| Free | 1 | 60 | 1000 | 10000 |
| Pro | 10 | 600 | 50000 | 1000000 |
| Enterprise | 100 | 6000 | 500000 | Unlimited |

---

## 八、部署架构

### 8.1 组件

```
┌─────────────────────────────────────────────────────────┐
│                      Clients                             │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              LLM Gateway (FastAPI)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Auth     │ │ Usage    │ │ Trace    │ │ Rate     │   │
│  │Middleware│ │Middleware│ │Middleware│ │ Limiter  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       │            │            │            │          │
│  ┌────▼────────────▼────────────▼────────────▼────┐     │
│  │              Router Engine                     │     │
│  └────┬────────────┬────────────┬───────────────┘     │
│       │            │            │                      │
│  ┌────▼────┐ ┌────▼────┐ ┌────▼────┐                 │
│  │ OpenAI  │ │ Claude  │ │  vLLM   │                 │
│  └─────────┘ └─────────┘ └─────────┘                 │
└───────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
   │PostgreSQL│ │  Redis   │ │  Kafka   │
   └─────────┘ └──────────┘ └─────────┘
```

### 8.2 Docker 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| DATABASE_URL | Yes | PostgreSQL 连接 |
| REDIS_URL | Yes | Redis 连接 |
| KAFKA_BOOTSTRAP_SERVERS | No | Kafka brokers |
| OPENAI_API_KEY | Yes | OpenAI API Key |
| ANTHROPIC_API_KEY | No | Claude API Key |
| VLLM_ENDPOINT | No | vLLM 端点 |
| SECRET_KEY | Yes | JWT 签名密钥 |
| GITHUB_CLIENT_ID | No | GitHub OAuth |
| GOOGLE_CLIENT_ID | No | Google OAuth |

---

## 九、待完成功能

| 功能 | 优先级 | 复杂度 | 预计工时 |
|------|--------|--------|----------|
| 配额管理（完整） | P1 | 中 | 4h |
| Azure OpenAI 接入 | P2 | 中 | 4h |
| 用量图表 | P1 | 低 | 2h |
| 计费报表 | P2 | 中 | 6h |
| OAuth 用户自动注册 | P1 | 中 | 4h |
| API 限流增强 | P1 | 低 | 2h |
| 日志查询界面 | P2 | 高 | 8h |

---

## 十、验收标准

### 10.1 API 兼容性

- [ ] OpenAI Chat Completions API 100% 兼容
- [ ] OpenAI Embeddings API 100% 兼容
- [ ] 支持 Streaming 和 non-streaming

### 10.2 路由能力

- [ ] 4 种路由策略均可正常工作
- [ ] Provider 故障时自动切换
- [ ] 路由决策有日志记录

### 10.3 多租户

- [ ] 租户隔离生效
- [ ] API Key 认证有效
- [ ] 配额限制生效

### 10.4 运维

- [ ] Docker 一键部署
- [ ] CI/CD 全流程通过
- [ ] Health Check 正常

---

## 十一、聊天渠道集成

### 11.1 Telegram Bot

| 功能 | 状态 | 说明 |
|------|------|------|
| Webhook 接收 | ✅ | `/webhook/telegram/{token}` |
| 自动回复 | ✅ | LLM 处理消息 |
| Markdown 支持 | ✅ | 格式解析 |
| 流式响应 | ✅ | typing indicator |
| 消息拆分 | ✅ | 超过 4096 字符自动拆分 |

**配置项：**
```bash
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_WEBHOOK_URL=https://domain.com/webhook/telegram/xxx
TELEGRAM_ALLOWED_CHATS=123,456
```

### 11.2 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/webhook/telegram/{token}` | POST | 接收 Telegram 更新 |
| `/webhook/telegram/setup` | GET | 设置 Webhook |
| `/webhook/telegram/info` | GET | Bot 信息 |
| `/webhook/telegram/send` | POST | 发送消息 |

---

## 十二、Rerank 模型

### 12.1 Provider

| Provider | 模型 | 状态 |
|----------|------|------|
| Cohere | rerank-english-v2.0 | ✅ |
| Cohere | rerank-multilingual-v2.0 | 🔄 |

### 12.2 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/rerank` | POST | 带认证的 Rerank |
| `/v1/rerank/simple` | POST | 测试用简化版 |

### 12.3 请求格式

```json
{
  "query": "search query",
  "documents": ["doc1", "doc2", ...],
  "model": "rerank-english-v2.0",
  "top_n": 3
}
```

### 12.4 响应格式

```json
{
  "id": "xxx",
  "results": [
    {"index": 0, "document": "doc1", "relevance_score": 0.95}
  ]
}
```

---

## 十三、功能完成度总览

### 13.1 核心功能 (Core)

| 模块 | 功能 | 状态 | 备注 |
|------|------|------|------|
| **API** | Chat Completions | ✅ | OpenAI 兼容 |
| | Embeddings | ✅ | |
| | Models List | ✅ | |
| | Streaming | ✅ | SSE |
| | Tool Calling | ✅ | |
| | Rerank | ✅ | Cohere |
| **Provider** | OpenAI | ✅ | |
| | Claude | ✅ | |
| | vLLM | ✅ | |
| | Azure OpenAI | ❌ | |
| **路由** | Cost 策略 | ✅ | |
| | Latency 策略 | ✅ | |
| | Quality 策略 | ✅ | |
| | Balanced 策略 | ✅ | |

### 13.2 多租户 (Multi-Tenant)

| 模块 | 功能 | 状态 | 备注 |
|------|------|------|------|
| | 租户管理 | ✅ | CRUD |
| | API Key | ✅ | 生成/撤销 |
| | 配额管理 | ✅ | 限额/用量 |
| | OAuth 注册 | ✅ | GitHub/Google |

### 13.3 计费 (Billing)

| 模块 | 功能 | 状态 | 备注 |
|------|------|------|------|
| | Token 计费 | ✅ | |
| | 用量记录 | ✅ | |
| | 成本统计 | ✅ | |
| | 计费报表 | ❌ | |

### 13.4 中间件 (Middleware)

| 模块 | 功能 | 状态 |
|------|------|------|
| | Auth | ✅ |
| | Rate Limit | ✅ |
| | Usage | ✅ |
| | Trace | ✅ |
| | Quota | ✅ |

### 13.5 渠道 (Channels)

| 模块 | 功能 | 状态 |
|------|------|------|
| | Telegram Bot | ✅ |
| | Discord | ❌ |
| | Slack | ❌ |

### 13.6 DevOps

| 模块 | 功能 | 状态 |
|------|------|------|
| | Docker | ✅ |
| | Docker Compose | ✅ |
| | CI/CD | ✅ |

---

## 十四、待完成功能

| 功能 | 优先级 | 复杂度 | 预计工时 |
|------|--------|--------|----------|
| Azure OpenAI 接入 | P2 | 中 | 4h |
| 计费报表 | P2 | 中 | 6h |
| Discord 渠道 | P2 | 低 | 2h |
| Slack 渠道 | P2 | 低 | 2h |
| Cohere Rerank v3 | P1 | 低 | 2h |
| 日志查询界面 | P2 | 高 | 8h |
| WebSocket 流式输出 | P1 | 中 | 4h |

---

## 十五、里程碑

| 阶段 | 内容 | 状态 |
|------|------|------|
| M1 | 核心 API + Provider + 路由 | ✅ 完成 |
| M2 | 多租户 + 计费 + 中间件 | ✅ 完成 |
| M3 | OAuth + Telegram + UI | ✅ 完成 |
| M4 | Rerank + 渠道扩展 | ✅ 完成 |
| M5 | Azure + 报表 + WebSocket | 🔄 进行中 |
