# LLM Gateway PRD - 产品需求文档

> **版本**: v1.0.0
> **更新**: 2026-04-01
> **状态**: ✅ 全部功能已完成

---

## 一、项目概述

### 目标
构建统一的 LLM 网关服务，支持多 Provider 路由、流式输出、多租户管理和计费。

### 核心能力
- 统一 API 接口（OpenAI 兼容）
- 多 Provider 自动路由与 Failover
- 流式响应（Server-Sent Events）
- 多租户隔离与计费
- WebSocket 实时对话
- Telegram/Discord/Slack 渠道集成

---

## 二、技术架构

### 技术栈
- **框架**: FastAPI + Python 3.11
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **Provider**: OpenAI, Anthropic Claude, vLLM, Azure OpenAI, Moonshot, Cohere
- **部署**: Docker + Docker Compose

### 目录结构
```
llm-gateway/
├── app/
│   ├── api/           # API 路由
│   ├── core/          # 核心配置
│   ├── models/        # 数据模型
│   ├── providers/     # LLM Provider 客户端
│   ├── services/      # 业务服务
│   └── main.py        # 应用入口
├── docker/            # Docker 配置
├── tests/             # 测试
└── docs/              # 文档
```

---

## 三、功能模块

### 1. 核心 API（7/7 完成）

| 功能 | 端点 | 状态 |
|------|------|------|
| Chat Completions | POST `/v1/chat/completions` | ✅ |
| Models List | GET `/v1/models` | ✅ |
| Embeddings | POST `/v1/embeddings` | ✅ |
| Rerank | POST `/v1/rerank` | ✅ |
| 流式输出 | Server-Sent Events | ✅ |
| 并发限制 | Token / Rate Limiting | ✅ |
| 健康检查 | GET `/health` | ✅ |

### 2. Provider 支持（4/4 完成）

| Provider | 状态 | 模型 |
|----------|------|------|
| OpenAI | ✅ | gpt-4o, gpt-4o-mini, gpt-35-turbo |
| Anthropic Claude | ✅ | claude-3-5-sonnet, claude-3-haiku |
| vLLM | ✅ | llama-3-70b, llama-3-8b, qwen-72b |
| Azure OpenAI | ✅ | gpt-4o, gpt-4o-mini, gpt-35-turbo |
| Moonshot | ✅ | moonshot-v1-8k, moonshot-v1-32k |
| Cohere Rerank | ✅ | rerank-english-v2.0, rerank-multilingual-v2.0 |

### 3. 路由引擎（4/4 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| 智能路由 | 按模型前缀路由到对应 Provider | ✅ |
| Failover | Provider 失败自动切换 | ✅ |
| 负载均衡 | 支持权重配置 | ✅ |
| 成本优化 | 按 token 用量计费 | ✅ |

### 4. 多租户（4/4 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| API Key 管理 | 生成、撤销、查询 | ✅ |
| 租户隔离 | 数据完全隔离 | ✅ |
| 使用配额 | 防止超出额度 | ✅ |
| 额度和告警 | 阈值告警 | ✅ |

### 5. 计费和用量（4/4 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| 用量记录 | 每次请求记录 | ✅ |
| 计费报表 | 按时间/模型/租户统计 | ✅ |
| 成本估算 | API 成本预览 | ✅ |
| Dashboard | Admin UI 可视化 | ✅ |

### 6. 中间件和安全（5/5 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| 认证 | API Key 验证 | ✅ |
| CORS | 跨域支持 | ✅ |
| 日志 | 请求/响应日志 | ✅ |
| 限流 | Rate Limiting | ✅ |
| 错误处理 | 统一异常处理 | ✅ |

### 7. 聊天渠道集成（3/3 完成）

| 渠道 | 功能 | 状态 |
|------|------|------|
| Telegram | Bot 命令式对话 | ✅ |
| Discord | Webhook 集成 | ✅ |
| Slack | App Mention 集成 | ✅ |

### 8. DevOps（3/3 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| Docker | 多阶段构建镜像 | ✅ |
| CI/CD | GitHub Actions | ✅ |
| Healthcheck | 容器健康检查 | ✅ |

### 9. 日志和监控（1/1 完成）

| 功能 | 说明 | 状态 |
|------|------|------|
| 日志查询 API | 分页/过滤/搜索 | ✅ |

---

## 四、API 文档

### Chat Completions
```bash
curl -X POST http://localhost:28000/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Rerank
```bash
curl -X POST http://localhost:28000/v1/rerank \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "documents": ["doc1", "doc2"]}'
```

### WebSocket
```javascript
const ws = new WebSocket("ws://localhost:28000/ws/v1/chat/stream");
ws.send(JSON.stringify({type: "auth", token: "sk-xxx"}));
ws.send(JSON.stringify({type: "chat", message: "Hello", model: "gpt-4o"}));
```

### Telegram
```
/start - 开始对话
/chat <message> - 与 AI 对话
/models - 查看可用模型
```

---

## 五、部署

### Docker Compose
```bash
cd docker && docker-compose up -d
```

### 环境变量
```bash
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
TELEGRAM_BOT_TOKEN=xxx
```

---

## 六、里程碑

| 阶段 | 完成日期 | 状态 |
|------|----------|------|
| M1: 核心 API + Provider | 2026-03-15 | ✅ |
| M2: 路由 + 多租户 | 2026-03-20 | ✅ |
| M3: 计费 + Dashboard | 2026-03-25 | ✅ |
| M4: 渠道集成 | 2026-04-01 | ✅ |
| M5: 优化 + 上线 | 2026-04-01 | ✅ |

---

**✅ 项目完成！所有功能已实现。**
