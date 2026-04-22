"""Integration test for async ManagedSessionManager + AIOrchestrator.

Tests:
  1. AsyncAnthropic client instantiation
  2. Single agent session creation + message + cleanup
  3. Parallel agent creation (5 concurrent)
  4. No thread exhaustion under parallel load

Usage:
    cd app/
    PYTHONPATH=. ../.venv/bin/python3 engine/agents/managed/test_async_integration.py

Requires: ANTHROPIC_API_KEY in environment (loaded from ../../.env).
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parents[4] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# Add app/ to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from anthropic import AsyncAnthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test_async")


# ── Test 1: AsyncAnthropic client ────────────────────────────────────

async def test_async_client():
    """Verify AsyncAnthropic can be instantiated and makes a basic call."""
    logger.info("TEST 1: AsyncAnthropic client instantiation")

    from engine.agents.managed.session_manager import ManagedSessionManager

    mgr = ManagedSessionManager()
    assert isinstance(mgr.client, AsyncAnthropic), (
        f"Expected AsyncAnthropic, got {type(mgr.client).__name__}"
    )
    logger.info("  Client type: %s", type(mgr.client).__name__)

    # Verify we can make a simple API call (list models or similar)
    # Just verify the client can create an agent and clean up
    agent = await mgr.client.beta.agents.create(
        name="test-async-migration",
        model="claude-sonnet-4-6",
        system="You are a test agent. Respond briefly.",
        tools=[],
    )
    logger.info("  Created test agent: %s", agent.id)

    # Clean up
    await mgr.client.beta.agents.archive(agent.id)
    logger.info("  Archived test agent")

    logger.info("TEST 1: PASSED")
    return True


# ── Test 2: Single session lifecycle ─────────────────────────────────

async def test_single_session():
    """Create one session, send one message, verify response, clean up."""
    logger.info("TEST 2: Single session lifecycle")

    from engine.agents.managed.session_manager import ManagedSessionManager

    mgr = ManagedSessionManager()

    # Create agent
    agent = await mgr.client.beta.agents.create(
        name="test-single-session",
        model="claude-sonnet-4-6",
        system="You are a test agent. When asked, respond with exactly: TEST_OK",
        tools=[],
    )
    logger.info("  Agent: %s", agent.id)

    # Create environment
    env = await mgr.client.beta.environments.create(
        name="test-env",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    logger.info("  Environment: %s", env.id)

    # Create session
    session = await mgr.client.beta.sessions.create(
        agent=agent.id,
        environment_id=env.id,
        title="Test Session",
    )
    logger.info("  Session: %s", session.id)

    # Send a message and stream response
    response_text = ""
    async with await mgr.client.beta.sessions.events.stream(session.id) as stream:
        await mgr.client.beta.sessions.events.send(
            session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": "Say TEST_OK"}],
            }],
        )

        async for event in stream:
            if event.type == "agent.message":
                for block in getattr(event, "content", []):
                    if hasattr(block, "text"):
                        response_text += block.text
            if event.type == "session.status_idle":
                break

    logger.info("  Response: %s", response_text[:100])
    assert "TEST_OK" in response_text, f"Expected TEST_OK in response, got: {response_text[:200]}"

    # Clean up
    await mgr.client.beta.sessions.archive(session.id)
    await mgr.client.beta.agents.archive(agent.id)
    logger.info("  Cleaned up")

    logger.info("TEST 2: PASSED")
    return True


# ── Test 3: Parallel agent creation (5 concurrent) ──────────────────

async def test_parallel_agents():
    """Create 5 agents in parallel — verify no resource exhaustion."""
    logger.info("TEST 3: Parallel agent creation (5 concurrent)")

    from engine.agents.managed.session_manager import ManagedSessionManager

    mgr = ManagedSessionManager()
    start = time.monotonic()

    agents = []
    sessions = []
    envs = []

    async def create_one(i: int):
        agent = await mgr.client.beta.agents.create(
            name=f"test-parallel-{i}",
            model="claude-sonnet-4-6",
            system=f"You are test agent {i}. Respond briefly.",
            tools=[],
        )
        env = await mgr.client.beta.environments.create(
            name=f"test-env-{i}",
            config={"type": "cloud", "networking": {"type": "unrestricted"}},
        )
        session = await mgr.client.beta.sessions.create(
            agent=agent.id,
            environment_id=env.id,
            title=f"Test Parallel {i}",
        )
        agents.append(agent)
        envs.append(env)
        sessions.append(session)
        logger.info("  Agent %d: %s session=%s", i, agent.id, session.id)

    # Create 5 in parallel
    await asyncio.gather(*[create_one(i) for i in range(5)])

    elapsed = time.monotonic() - start
    logger.info("  Created 5 agents in %.1fs", elapsed)

    assert len(agents) == 5, f"Expected 5 agents, got {len(agents)}"
    assert len(sessions) == 5, f"Expected 5 sessions, got {len(sessions)}"

    # Send messages to all 5 in parallel
    start2 = time.monotonic()

    async def send_one(i: int, session_id: str):
        response_text = ""
        async with await mgr.client.beta.sessions.events.stream(session_id) as stream:
            await mgr.client.beta.sessions.events.send(
                session_id,
                events=[{
                    "type": "user.message",
                    "content": [{"type": "text", "text": f"Say AGENT_{i}_OK"}],
                }],
            )
            async for event in stream:
                if event.type == "agent.message":
                    for block in getattr(event, "content", []):
                        if hasattr(block, "text"):
                            response_text += block.text
                if event.type == "session.status_idle":
                    break
        logger.info("  Agent %d responded: %s", i, response_text[:50])
        return response_text

    responses = await asyncio.gather(*[
        send_one(i, s.id) for i, s in enumerate(sessions)
    ])

    elapsed2 = time.monotonic() - start2
    logger.info("  5 parallel messages in %.1fs", elapsed2)

    # Verify all responded
    for i, resp in enumerate(responses):
        assert f"AGENT_{i}_OK" in resp, f"Agent {i} didn't respond correctly: {resp[:100]}"

    # Clean up all
    for session in sessions:
        try:
            await mgr.client.beta.sessions.archive(session.id)
        except Exception:
            pass
    for agent in agents:
        try:
            await mgr.client.beta.agents.archive(agent.id)
        except Exception:
            pass

    logger.info("  Cleaned up 5 agents")
    logger.info("TEST 3: PASSED (total: %.1fs)", time.monotonic() - start)
    return True


# ── Main ─────────────────────────────────────────────────────────────

async def main():
    """Run all tests."""
    results = {}

    # Test 1: Client instantiation
    try:
        results["test_async_client"] = await test_async_client()
    except Exception as e:
        logger.error("TEST 1 FAILED: %s", e)
        results["test_async_client"] = False

    # Test 2: Single session lifecycle
    try:
        results["test_single_session"] = await test_single_session()
    except Exception as e:
        logger.error("TEST 2 FAILED: %s", e)
        results["test_single_session"] = False

    # Test 3: Parallel agents
    try:
        results["test_parallel_agents"] = await test_parallel_agents()
    except Exception as e:
        logger.error("TEST 3 FAILED: %s", e)
        results["test_parallel_agents"] = False

    # Summary
    print("\n" + "=" * 60)
    print("ASYNC MIGRATION TEST RESULTS")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")
    print(f"\n  {passed}/{total} tests passed")
    print("=" * 60)

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
