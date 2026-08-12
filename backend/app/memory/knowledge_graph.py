"""
Neo4j Knowledge Graph — organizational relationship memory.
Tracks agents, projects, tasks, repositories, deployments, and incidents.
"""
from typing import Optional, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

_driver: Optional[AsyncDriver] = None


async def init_neo4j() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    # Verify connectivity
    async with _driver.session() as session:
        await session.run("RETURN 1")
    # Create indexes
    await _create_indexes()


async def close_neo4j() -> None:
    if _driver:
        await _driver.close()


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j not initialized.")
    return _driver


async def _create_indexes() -> None:
    """Create Neo4j indexes and constraints."""
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Deployment) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.org_id)",
        "CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.project_id)",
    ]
    async with get_driver().session() as session:
        for q in queries:
            await session.run(q)


# ─── Node Operations ──────────────────────────────────────────────────────────
async def upsert_agent(agent_id: str, agent_type: str, name: str, org_id: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MERGE (a:Agent {id: $id})
            SET a.type = $type, a.name = $name, a.org_id = $org_id
            """,
            id=agent_id, type=agent_type, name=name, org_id=org_id,
        )


async def upsert_project(project_id: str, name: str, org_id: str, status: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MERGE (p:Project {id: $id})
            SET p.name = $name, p.org_id = $org_id, p.status = $status
            """,
            id=project_id, name=name, org_id=org_id, status=status,
        )


async def upsert_task(task_id: str, title: str, project_id: str, agent_type: str, status: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MERGE (t:Task {id: $task_id})
            SET t.title = $title, t.project_id = $project_id,
                t.agent_type = $agent_type, t.status = $status
            WITH t
            MATCH (p:Project {id: $project_id})
            MERGE (p)-[:HAS_TASK]->(t)
            """,
            task_id=task_id, title=title, project_id=project_id,
            agent_type=agent_type, status=status,
        )


# ─── Relationship Operations ──────────────────────────────────────────────────
async def agent_manages_project(agent_id: str, project_id: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MATCH (a:Agent {id: $agent_id}), (p:Project {id: $project_id})
            MERGE (a)-[:MANAGES]->(p)
            """,
            agent_id=agent_id, project_id=project_id,
        )


async def agent_assigned_to_task(agent_id: str, task_id: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MATCH (a:Agent {id: $agent_id}), (t:Task {id: $task_id})
            MERGE (a)-[:ASSIGNED_TO]->(t)
            """,
            agent_id=agent_id, task_id=task_id,
        )


async def task_depends_on(task_id: str, depends_on_id: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MATCH (t:Task {id: $task_id}), (d:Task {id: $depends_on_id})
            MERGE (t)-[:DEPENDS_ON]->(d)
            """,
            task_id=task_id, depends_on_id=depends_on_id,
        )


async def task_created_pr(task_id: str, pr_id: str, pr_url: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MERGE (pr:PullRequest {id: $pr_id, url: $pr_url})
            WITH pr
            MATCH (t:Task {id: $task_id})
            MERGE (t)-[:CREATED]->(pr)
            """,
            task_id=task_id, pr_id=pr_id, pr_url=pr_url,
        )


async def deployment_caused_incident(deployment_id: str, incident_id: str) -> None:
    async with get_driver().session() as session:
        await session.run(
            """
            MATCH (d:Deployment {id: $dep_id}), (i:Incident {id: $inc_id})
            MERGE (d)-[:CAUSED]->(i)
            """,
            dep_id=deployment_id, inc_id=incident_id,
        )


# ─── Query Operations ─────────────────────────────────────────────────────────
async def get_project_graph(project_id: str) -> list[dict]:
    """Retrieve the full relationship graph for a project."""
    async with get_driver().session() as session:
        result = await session.run(
            """
            MATCH path = (p:Project {id: $project_id})-[*1..4]-()
            RETURN path
            LIMIT 100
            """,
            project_id=project_id,
        )
        records = await result.data()
        return records


async def get_agent_history(agent_type: str, org_id: str, limit: int = 20) -> list[dict]:
    """Get tasks an agent has worked on."""
    async with get_driver().session() as session:
        result = await session.run(
            """
            MATCH (a:Agent {type: $agent_type, org_id: $org_id})-[:ASSIGNED_TO]->(t:Task)
            RETURN t.id as task_id, t.title as title, t.status as status
            ORDER BY t.created_at DESC
            LIMIT $limit
            """,
            agent_type=agent_type, org_id=org_id, limit=limit,
        )
        return await result.data()
