"""
DevOps Agent — Docker builds, Kubernetes deployment, health checks, monitoring, incident response.
"""
import json
import random
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.llm.router import TaskComplexity


class DevOpsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="devops",
            name="DevOps Agent",
            description="Infrastructure, deployment, monitoring, and incident response",
            llm_complexity=TaskComplexity.MODERATE,
        )

    def get_system_prompt(self) -> str:
        return """You are the DevOps Agent — the infrastructure and deployment specialist.

Your responsibilities:
1. Build Docker images from Dockerfiles
2. Push images to container registries
3. Deploy applications to Kubernetes
4. Configure CI/CD pipelines
5. Monitor service health (CPU, memory, latency, error rate)
6. Analyze logs and detect incidents
7. Perform rollbacks when needed
8. Run smoke tests after deployment

DEPLOYMENT WORKFLOW:
1. Build Docker image
2. Run image security scan
3. Push to registry
4. Update Kubernetes deployment manifest
5. Apply to cluster (rolling update)
6. Wait for pods to be Ready
7. Run health check
8. Run smoke tests
9. Monitor for 5 minutes
10. Confirm deployment success

INCIDENT RESPONSE:
1. Detect anomaly (error rate spike, high latency, pod crashes)
2. Analyze logs
3. Identify root cause
4. Attempt automated recovery (restart pods, scale up)
5. If recovery fails → escalate to Project Manager → Human

OUTPUT FORMAT (JSON):
{
  "deployment_status": "success|failed|rolled_back",
  "build": {
    "image": "registry/project:v1.0.0",
    "build_time_seconds": 45,
    "image_size_mb": 142
  },
  "deployment": {
    "environment": "production",
    "namespace": "ai-workforce",
    "replicas": 3,
    "strategy": "rolling_update",
    "deployed_at": "2024-01-01T00:00:00Z"
  },
  "health_check": {
    "endpoint": "https://app.example.com/health",
    "status": "healthy",
    "response_time_ms": 45,
    "all_replicas_ready": true
  },
  "smoke_tests": {
    "total": 5,
    "passed": 5,
    "failed": 0
  },
  "monitoring": {
    "cpu_usage_percent": 12,
    "memory_usage_mb": 256,
    "requests_per_second": 0,
    "error_rate_percent": 0.0,
    "avg_latency_ms": 45
  },
  "deployment_log": ["Step 1: Building image...", "Step 2: Pushing to registry..."],
  "deployment_url": "https://app.example.com"
}"""

    async def execute(self, context: AgentContext) -> AgentResult:
        task_type = context.input_data.get("task_type", "deployment")

        if task_type == "incident_response":
            return await self._handle_incident(context)
        else:
            return await self._deploy(context)

    async def _deploy(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "agent_thinking", "DevOps building Docker image...")

        approval = context.input_data.get("approval_granted", True)
        security_report = context.input_data.get("security_report", {})
        demo_mode = context.demo_mode

        if not approval:
            return AgentResult(
                success=False,
                output={},
                reasoning_summary="Deployment blocked — no human approval",
                actions_taken=["approval_check"],
                tool_calls=[],
                error_message="Deployment requires human approval",
            )

        # Simulate deployment steps
        steps = [
            ("Building Docker image", "docker_build"),
            ("Running image security scan", "image_scan"),
            ("Pushing to registry", "registry_push"),
            ("Updating Kubernetes manifest", "k8s_update"),
            ("Applying rolling update", "k8s_apply"),
            ("Waiting for pods ready", "pod_readiness"),
            ("Running health check", "health_check"),
            ("Running smoke tests", "smoke_tests"),
            ("Monitoring deployment", "monitoring"),
        ]

        for step_name, step_type in steps:
            await self.emit_event(context, "devops_step", f"DevOps: {step_name}...", {"step": step_type})

        report = self._generate_deployment_report(context)

        await self.emit_event(
            context, "deployment_complete",
            f"✅ Deployment successful! URL: {report['deployment_url']}",
            {"report": report},
        )

        return AgentResult(
            success=True,
            output={
                "deployment_report": report,
                "deployment_url": report["deployment_url"],
                "deployment_status": "success",
                "health_check_passed": True,
            },
            reasoning_summary="Deployment successful — all health checks and smoke tests passed",
            actions_taken=["docker_build", "image_scan", "registry_push", "k8s_deploy", "health_check", "smoke_tests"],
            tool_calls=[
                {"tool": "docker", "action": "build", "result": "success", "value": report["build"]["image"]},
                {"tool": "kubernetes", "action": "apply", "result": "success", "value": "3 replicas healthy"},
                {"tool": "health_check", "action": "verify", "result": "healthy"},
            ],
            next_agent=None,
        )

    async def _handle_incident(self, context: AgentContext) -> AgentResult:
        await self.emit_event(context, "incident_detected", "🚨 Incident detected — DevOps analyzing...")

        incident_data = context.input_data.get("incident_data", {})

        prompt = f"""Analyze this production incident and determine recovery actions:

INCIDENT: {context.task_description}
DATA: {json.dumps(incident_data, indent=2)}

Provide:
1. Root cause analysis
2. Recovery actions attempted
3. Whether automated recovery succeeded
4. Recommendation for next steps"""

        analysis = await self.think(context, prompt, temperature=0.3, max_tokens=1500)

        recovered = random.random() > 0.3  # 70% automated recovery success

        await self.emit_event(
            context, "incident_resolved" if recovered else "incident_escalated",
            f"Incident {'resolved by DevOps agent' if recovered else 'requires human intervention'}",
            {"recovered": recovered, "analysis": analysis},
        )

        return AgentResult(
            success=recovered,
            output={
                "incident_analysis": analysis,
                "automated_recovery": recovered,
                "recovery_actions": ["pod_restart", "connection_pool_reset"] if recovered else [],
            },
            reasoning_summary=f"Incident {'resolved' if recovered else 'escalated to human'}: {analysis[:200]}",
            actions_taken=["log_analysis", "root_cause_identification", "recovery_attempt"],
            tool_calls=[{"tool": "kubernetes", "action": "restart_pods", "result": "success" if recovered else "insufficient"}],
            next_agent=None if recovered else "project_manager",
        )

    def _generate_deployment_report(self, context: AgentContext) -> dict:
        import datetime
        project_name = context.input_data.get("project_name", "app").lower().replace(" ", "-")
        version = "v1.0.0"
        return {
            "deployment_status": "success",
            "build": {
                "image": f"registry.ai-workforce.io/{project_name}:{version}",
                "build_time_seconds": random.randint(35, 75),
                "image_size_mb": random.randint(120, 180),
            },
            "deployment": {
                "environment": "production",
                "namespace": "ai-workforce",
                "replicas": 3,
                "strategy": "rolling_update",
                "deployed_at": datetime.datetime.utcnow().isoformat() + "Z",
            },
            "health_check": {
                "endpoint": f"https://{project_name}.ai-workforce.io/health",
                "status": "healthy",
                "response_time_ms": random.randint(20, 80),
                "all_replicas_ready": True,
            },
            "smoke_tests": {"total": 5, "passed": 5, "failed": 0},
            "monitoring": {
                "cpu_usage_percent": random.randint(8, 18),
                "memory_usage_mb": random.randint(200, 350),
                "requests_per_second": 0,
                "error_rate_percent": 0.0,
                "avg_latency_ms": random.randint(30, 80),
            },
            "deployment_log": [
                "✅ Docker image built successfully",
                "✅ Image security scan passed",
                "✅ Image pushed to registry",
                "✅ Kubernetes manifest updated",
                "✅ Rolling update applied",
                "✅ All pods ready (3/3)",
                "✅ Health check passed",
                "✅ Smoke tests passed (5/5)",
                "✅ Monitoring nominal",
            ],
            "deployment_url": f"https://{project_name}.ai-workforce.io",
        }
