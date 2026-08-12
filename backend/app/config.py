"""
Autonomous Enterprise AI Workforce — Configuration
All settings loaded from environment variables via Pydantic Settings.
"""
from functools import lru_cache
from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ──────────────────────────────────────────
    app_name: str = "Autonomous Enterprise AI Workforce"
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change_me_in_production"
    debug: bool = True
    log_level: str = "INFO"
    demo_mode: bool = True

    # ─── JWT Auth ─────────────────────────────────────────────
    jwt_secret: str = "change_me_jwt_secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ─── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://ai_workforce:secret@localhost:5432/ai_workforce"
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # ─── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # ─── Neo4j ────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "neo4j_secret"

    # ─── LLM Providers ────────────────────────────────────────
    llm_provider: Literal["openai", "groq", "azure", "bedrock"] = "groq"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_fast_model: str = "gpt-4o-mini"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # AWS Bedrock
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_bedrock_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # ─── Embeddings ───────────────────────────────────────────
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # ─── GitHub ───────────────────────────────────────────────
    github_token: str = ""
    github_org: str = ""
    github_default_repo: str = "ai-workforce-projects"

    # ─── Slack ────────────────────────────────────────────────
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_notification_channel: str = "#ai-workforce"

    # ─── Email ────────────────────────────────────────────────
    email_provider: str = "smtp"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    sendgrid_api_key: str = ""

    # ─── Frontend / CORS ──────────────────────────────────────
    allowed_origins: str = "http://localhost:3000"
    next_public_api_url: str = "http://localhost:8000"

    # ─── Agent Limits ─────────────────────────────────────────
    max_concurrent_agents: int = 10
    max_agent_retries: int = 3
    max_task_retries: int = 5
    max_workflow_retries: int = 2
    max_tool_calls_per_task: int = 50
    max_llm_calls_per_task: int = 30

    # ─── Cost Limits (USD) ────────────────────────────────────
    default_project_budget: float = 10.00
    default_agent_budget: float = 3.00
    default_task_budget: float = 1.00
    cost_alert_threshold: float = 0.80

    # ─── Security ─────────────────────────────────────────────
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    enable_audit_log: bool = True

    # ─── Monitoring ───────────────────────────────────────────
    prometheus_port: int = 9090
    grafana_password: str = "admin"

    @field_validator("allowed_origins")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v  # kept as string; split in main.py

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_llm_model(self) -> str:
        mapping = {
            "openai": self.openai_model,
            "groq": self.groq_model,
            "azure": self.azure_openai_deployment,
            "bedrock": self.aws_bedrock_model,
        }
        return mapping.get(self.llm_provider, self.groq_model)

    @property
    def active_fast_model(self) -> str:
        mapping = {
            "openai": self.openai_fast_model,
            "groq": self.groq_fast_model,
            "azure": self.azure_openai_deployment,
            "bedrock": self.aws_bedrock_model,
        }
        return mapping.get(self.llm_provider, self.groq_fast_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
