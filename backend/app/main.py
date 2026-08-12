"""
FastAPI Application Entry Point
Autonomous Enterprise AI Workforce
"""
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.database import init_db, close_db
from app.memory.short_term import init_redis, close_redis
from app.memory.knowledge_graph import init_neo4j, close_neo4j

# ─── Import Routers ───────────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.agents import router as agents_router
from app.api.approvals import router as approvals_router
from app.api.audit import router as audit_router
from app.api.costs import router as costs_router
from app.api.websocket import router as ws_router
from app.api.health import router as health_router
from app.api.demo import router as demo_router
from app.api.documents import router as documents_router
from app.api.metrics import router as metrics_router

# ─── Logging Setup ────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

log = structlog.get_logger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management."""
    log.info("🚀 Starting Autonomous Enterprise AI Workforce...")

    # Initialize connections
    await init_db()
    log.info("✅ PostgreSQL connected and tables created")

    await init_redis()
    log.info("✅ Redis connected")

    await init_neo4j()
    log.info("✅ Neo4j connected")

    log.info(
        "🤖 AI Workforce ready",
        provider=settings.llm_provider,
        model=settings.active_llm_model,
        demo_mode=settings.demo_mode,
    )

    yield

    # Cleanup
    await close_db()
    await close_redis()
    await close_neo4j()
    log.info("👋 Autonomous Enterprise AI Workforce shutdown complete")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Autonomous Enterprise AI Workforce",
    description="""
    ## AI Workforce OS

    A production-grade multi-agent AI Operating System where specialized AI agents
    collaborate autonomously to execute enterprise business objectives.

    ### Agents
    - 🧠 **CEO Agent** — Strategic analysis & delegation
    - 📋 **Project Manager** — Task planning & coordination
    - 💻 **Developer** — Code generation & GitHub operations
    - 🧪 **QA Agent** — Testing & quality assurance
    - 🔒 **Security Agent** — SAST, dependency scanning
    - 🚀 **DevOps Agent** — Deployment & monitoring
    - 📚 **Documentation** — Automated docs generation
    - 🎧 **Support Agent** — RAG-powered customer support
    - 🔬 **Research Agent** — Technology research
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Prometheus Metrics ────────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ─── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(health_router, prefix=API_PREFIX, tags=["Health"])
app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(projects_router, prefix=f"{API_PREFIX}/projects", tags=["Projects"])
app.include_router(tasks_router, prefix=f"{API_PREFIX}/tasks", tags=["Tasks"])
app.include_router(agents_router, prefix=f"{API_PREFIX}/agents", tags=["Agents"])
app.include_router(approvals_router, prefix=f"{API_PREFIX}/approvals", tags=["Approvals"])
app.include_router(audit_router, prefix=f"{API_PREFIX}/audit", tags=["Audit"])
app.include_router(costs_router, prefix=f"{API_PREFIX}/costs", tags=["Costs"])
app.include_router(documents_router, prefix=f"{API_PREFIX}/documents", tags=["Knowledge Base"])
app.include_router(metrics_router, prefix=f"{API_PREFIX}/metrics", tags=["Metrics"])
app.include_router(demo_router, prefix=f"{API_PREFIX}/demo", tags=["Demo"])
app.include_router(ws_router, prefix=f"{API_PREFIX}/ws", tags=["WebSocket"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "tagline": "A Virtual Company Powered by Autonomous AI Agents.",
        "docs": "/docs",
        "status": "operational",
        "demo_mode": settings.demo_mode,
    }
