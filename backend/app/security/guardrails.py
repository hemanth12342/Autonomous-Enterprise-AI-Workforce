"""
Guardrails — blocks dangerous operations before agents can execute them.
Implements input/output validation and prompt injection detection.
"""
import re
from typing import Any

# ─── Dangerous SQL patterns ───────────────────────────────────────────────────
DANGEROUS_SQL_PATTERNS = [
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)",  # DELETE without WHERE
    r"\bALTER\s+TABLE\b.*\bDROP\b",
]

# ─── Dangerous shell commands ──────────────────────────────────────────────────
DANGEROUS_SHELL_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bformat\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r":(){:|:&};:",  # fork bomb
]

# ─── Prompt injection keywords ────────────────────────────────────────────────
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(everything|all)\s+above",
    r"you\s+are\s+now\s+(?!an?\s+(AI|assistant))",
    r"disregard\s+your\s+(system\s+)?prompt",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"DAN\s+mode",
]

# ─── Secret patterns (detect accidental exposure) ─────────────────────────────
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",           # OpenAI API key
    r"gsk_[A-Za-z0-9]{20,}",          # Groq API key
    r"ghp_[A-Za-z0-9]{36}",           # GitHub PAT
    r"xoxb-[0-9]+-[A-Za-z0-9-]+",    # Slack bot token
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",  # JWT
    r"AKIA[0-9A-Z]{16}",               # AWS Access Key
]

# ─── Production-destructive operation blocklist ───────────────────────────────
BLOCKED_PRODUCTION_OPERATIONS = {
    "drop_database",
    "delete_production_resources",
    "truncate_table",
    "destroy_cluster",
    "delete_all_records",
    "format_disk",
}


class GuardrailViolation(Exception):
    """Raised when a guardrail blocks an operation."""
    def __init__(self, reason: str, severity: str = "critical"):
        self.reason = reason
        self.severity = severity
        super().__init__(f"[GUARDRAIL BLOCKED] {severity.upper()}: {reason}")


class Guardrails:
    """Central guardrail engine — validates all agent inputs and outputs."""

    @staticmethod
    def check_sql(query: str) -> None:
        """Block dangerous SQL statements."""
        for pattern in DANGEROUS_SQL_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise GuardrailViolation(
                    f"Dangerous SQL pattern detected: {pattern}",
                    severity="critical",
                )

    @staticmethod
    def check_shell_command(command: str) -> None:
        """Block dangerous shell commands."""
        for pattern in DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise GuardrailViolation(
                    f"Dangerous shell command blocked: {command[:80]}",
                    severity="critical",
                )

    @staticmethod
    def check_prompt_injection(text: str) -> None:
        """Detect prompt injection attempts in user-provided input."""
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise GuardrailViolation(
                    f"Potential prompt injection detected",
                    severity="high",
                )

    @staticmethod
    def check_for_secrets(text: str) -> list[str]:
        """Scan text for accidentally exposed secrets. Returns list of findings."""
        findings = []
        for pattern in SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                findings.append(f"Potential secret pattern found: {pattern}")
        return findings

    @staticmethod
    def check_production_operation(operation: str, environment: str = "production") -> None:
        """Block destructive operations in production without approval."""
        if environment == "production" and operation in BLOCKED_PRODUCTION_OPERATIONS:
            raise GuardrailViolation(
                f"Operation '{operation}' is blocked in production environment. "
                "Requires explicit human approval override.",
                severity="critical",
            )

    @staticmethod
    def validate_agent_output(output: Any, agent_type: str) -> dict:
        """
        Validate agent output for secrets exposure.
        Returns sanitized output with a findings report.
        """
        output_str = str(output)
        secret_findings = Guardrails.check_for_secrets(output_str)

        return {
            "is_safe": len(secret_findings) == 0,
            "secret_findings": secret_findings,
            "agent_type": agent_type,
        }

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Remove any detected secret patterns from text."""
        sanitized = text
        for pattern in SECRET_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)
        return sanitized


# ─── Global instance ──────────────────────────────────────────────────────────
guardrails = Guardrails()
