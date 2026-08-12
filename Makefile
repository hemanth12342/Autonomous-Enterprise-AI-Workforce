.PHONY: help dev build test migrate clean logs shell

# ─────────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Autonomous Enterprise AI Workforce"
	@echo "  ===================================="
	@echo ""
	@echo "  make dev          Start all services (Docker Compose)"
	@echo "  make dev-lite     Start only core services (no monitoring)"
	@echo "  make build        Build all Docker images"
	@echo "  make stop         Stop all services"
	@echo "  make clean        Remove containers, volumes, images"
	@echo "  make logs         Tail all service logs"
	@echo "  make logs-be      Tail backend logs"
	@echo "  make logs-fe      Tail frontend logs"
	@echo "  make migrate      Run database migrations"
	@echo "  make seed         Seed demo data"
	@echo "  make test         Run all tests"
	@echo "  make test-be      Run backend tests"
	@echo "  make shell-be     Shell into backend container"
	@echo "  make shell-db     Shell into PostgreSQL"
	@echo "  make setup        First-time setup (copy .env, install deps)"
	@echo ""

# ─────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────
setup:
	@echo "→ Copying .env.example to .env..."
	@cp -n .env.example .env || echo ".env already exists, skipping."
	@echo "→ Done. Edit .env with your API keys before running make dev."

# ─────────────────────────────────────────────────
# DEVELOPMENT
# ─────────────────────────────────────────────────
dev:
	docker compose up --build

dev-detach:
	docker compose up --build -d

dev-lite:
	docker compose up --build postgres redis backend frontend

stop:
	docker compose down

restart:
	docker compose restart

# ─────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────
build:
	docker compose build --no-cache

build-backend:
	docker compose build --no-cache backend

build-frontend:
	docker compose build --no-cache frontend

# ─────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

migrate-rollback:
	docker compose exec backend alembic downgrade -1

seed:
	docker compose exec backend python -m app.scripts.seed_demo

shell-db:
	docker compose exec postgres psql -U ai_workforce -d ai_workforce

# ─────────────────────────────────────────────────
# TESTING
# ─────────────────────────────────────────────────
test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

test-be:
	docker compose exec backend pytest tests/unit/ -v

test-integration:
	docker compose exec backend pytest tests/integration/ -v

test-agents:
	docker compose exec backend pytest tests/agents/ -v

# ─────────────────────────────────────────────────
# LOGS
# ─────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-be:
	docker compose logs -f backend

logs-fe:
	docker compose logs -f frontend

logs-worker:
	docker compose logs -f worker

# ─────────────────────────────────────────────────
# SHELLS
# ─────────────────────────────────────────────────
shell-be:
	docker compose exec backend bash

shell-fe:
	docker compose exec frontend sh

# ─────────────────────────────────────────────────
# CLEAN
# ─────────────────────────────────────────────────
clean:
	docker compose down -v --rmi local
	@echo "→ Cleaned all containers, volumes, and local images."

clean-all:
	docker compose down -v --rmi all
	@echo "→ Cleaned everything including pulled images."

# ─────────────────────────────────────────────────
# PRODUCTION
# ─────────────────────────────────────────────────
k8s-deploy:
	kubectl apply -f infrastructure/kubernetes/

k8s-status:
	kubectl get all -n ai-workforce

k8s-delete:
	kubectl delete -f infrastructure/kubernetes/
