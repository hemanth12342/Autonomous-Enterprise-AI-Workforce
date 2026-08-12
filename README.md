# Autonomous Enterprise AI Workforce

> **"A Virtual Company Powered by Autonomous AI Agents."**

A production-grade **multi-agent AI Operating System** where specialized AI agents collaborate autonomously to execute enterprise business objectives — from planning to deployment.

---

## What This Is

This is **not** a chatbot. This is an AI Operating System.

You give it a business objective. A team of specialized AI agents breaks it down, assigns work, writes code, tests it, secures it, documents it, deploys it, monitors it, and reports back.

```
Human: "Build an AI-powered customer support platform."

CEO Agent → analyzes objective
Project Manager → creates 12 tasks, builds DAG
Research Agent → recommends architecture  
Developer Agent → writes code, creates PRs
QA Agent → tests, finds 2 failures, reports back
Developer Agent → fixes failures
Security Agent → scans, finds 1 medium issue, fixed
Documentation Agent → generates README, API docs
Human ← "Deployment ready. Awaiting approval."
Human → APPROVE
DevOps Agent → builds Docker, deploys to K8s
Monitoring → health checks pass
CEO Agent → final executive report
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Orchestration** | LangGraph (stateful agent graphs) |
| **Backend** | Python 3.11 + FastAPI |
| **Frontend** | Next.js 14 + TypeScript |
| **Primary DB** | PostgreSQL 16 + pgvector |
| **Cache/Queue** | Redis 7 |
| **Knowledge Graph** | Neo4j 5 |
| **LLM Providers** | OpenAI, Groq, Azure OpenAI (abstracted) |
| **RAG** | pgvector + sentence-transformers |
| **Auth** | JWT + OAuth2 |
| **Monitoring** | Prometheus + Grafana |
| **Containers** | Docker + Kubernetes |

---

## AI Agents

| Agent | Role |
|---|---|
| 🧠 **CEO Agent** | Strategic analysis, delegation, final reports |
| 📋 **Project Manager** | Task planning, DAG creation, coordination |
| 💻 **Developer** | Code generation, GitHub operations, bug fixing |
| 🧪 **QA Agent** | Test generation, execution, quality reports |
| 🔒 **Security Agent** | SAST, dependency scan, secret detection |
| 🚀 **DevOps Agent** | Docker, Kubernetes, deployment, monitoring |
| 📚 **Documentation** | README, API docs, architecture guides |
| 🎧 **Support Agent** | RAG-powered customer support |
| 🔬 **Research Agent** | Technology research, analysis, recommendations |

---

## Quick Start

### Prerequisites
- Docker Desktop ≥ 24.0
- Docker Compose v2.20+
- 8GB RAM available for Docker

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/autonomous-enterprise-ai.git
cd autonomous-enterprise-ai

# Copy environment template
make setup

# Edit .env with your API keys
nano .env
```

### 2. Start Everything

```bash
make dev
```

This starts: PostgreSQL, Redis, Neo4j, Backend API, Worker, Frontend, Prometheus, Grafana.

### 3. Access Services

| Service | URL |
|---|---|
| 🌐 **Dashboard** | http://localhost:3000 |
| 🔧 **API** | http://localhost:8000 |
| 📖 **API Docs** | http://localhost:8000/docs |
| 🗄️ **Neo4j Browser** | http://localhost:7474 |
| 📊 **Grafana** | http://localhost:3001 |
| 📈 **Prometheus** | http://localhost:9090 |

### 4. Run the Demo

Click **"Start Autonomous Company"** on the dashboard, or:

```bash
make seed  # Load demo data
```

---

## Project Structure

```
autonomous-enterprise-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── agents/           # 9 specialized AI agents
│   │   │   ├── ceo/
│   │   │   ├── project_manager/
│   │   │   ├── developer/
│   │   │   ├── qa/
│   │   │   ├── devops/
│   │   │   ├── security/
│   │   │   ├── documentation/
│   │   │   ├── support/
│   │   │   └── research/
│   │   ├── orchestration/    # LangGraph workflow engine
│   │   ├── memory/           # Redis + PostgreSQL + Neo4j
│   │   ├── rag/              # Document ingestion + retrieval
│   │   ├── tools/            # GitHub, Slack, deployment tools
│   │   ├── mcp/              # Model Context Protocol servers
│   │   ├── llm/              # LLM provider abstraction
│   │   ├── security/         # Auth, RBAC, guardrails
│   │   ├── models/           # SQLAlchemy ORM models
│   │   └── config.py
│   ├── tests/
│   ├── alembic/              # Database migrations
│   └── Dockerfile
├── frontend/                 # Next.js 14 dashboard
│   ├── src/app/              # App Router pages
│   └── src/components/       # Reusable UI components
├── infrastructure/
│   ├── docker/               # Prometheus, Grafana configs
│   ├── kubernetes/           # K8s manifests
│   └── terraform/            # Cloud infrastructure (optional)
├── mcp-servers/              # MCP server implementations
├── docs/                     # Architecture & deployment guides
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## Key Features

### 🤖 Autonomous Agent Workflow
- CEO breaks down business objectives
- Project Manager builds dependency graphs (DAGs)
- Agents execute in parallel where possible
- Automatic retry + failure recovery loops
- Human approval gates for high-risk actions

### 🧠 Memory Architecture
- **Short-term**: Redis (task state, agent context)
- **Long-term**: PostgreSQL + pgvector (project history, embeddings)
- **Knowledge Graph**: Neo4j (agent/project/task relationships)

### 🔍 Enterprise RAG
- Ingest PDF, DOCX, MD, CSV, web pages
- pgvector similarity search
- Metadata filtering (department, project, access level)
- Citation-grounded answers

### 🔐 Security
- JWT authentication + RBAC
- Agent permission profiles (no unlimited access)
- Guardrails blocking dangerous operations
- Secret detection in generated code
- Immutable audit logs

### 💰 Cost Tracking
- Per-agent, per-project, per-model cost breakdown
- Configurable budgets with automatic stops
- Model routing (fast/cheap vs. powerful models)
- Semantic caching

### 📊 Observability
- Real-time WebSocket event stream
- Prometheus metrics
- Grafana dashboards
- OpenTelemetry tracing
- Structured JSON logging

---

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

Required minimum:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
JWT_SECRET=your_long_secret
POSTGRES_PASSWORD=strong_password
```

---

## Development

```bash
make dev          # Start all services
make logs-be      # Backend logs
make migrate      # Run DB migrations
make test         # Run all tests
make shell-be     # Shell into backend
```

---

## Deployment

### Docker Compose (Local)
```bash
make dev
```

### Kubernetes (Production)
```bash
make k8s-deploy
```

See [`docs/deployment.md`](docs/deployment.md) for full production deployment guide.

---

## Documentation

| Document | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System architecture |
| [`docs/agents.md`](docs/agents.md) | Agent specifications |
| [`docs/api.md`](docs/api.md) | API reference |
| [`docs/deployment.md`](docs/deployment.md) | Deployment guide |
| [`docs/security.md`](docs/security.md) | Security model |

---

## License

MIT License. See [LICENSE](LICENSE).
