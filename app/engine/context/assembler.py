"""Context Assembly Service — builds LLM-ready context from SIM run data.

Every LLM consumer (judgment, leader agents, Argus, narrative) requests
context through this service. Provides:
- Named blocks with defined scope and caching
- Visibility filtering (information asymmetry)
- DB-stored methodology (moderator-editable)

Source: SEED_D9_CONTEXT_ASSEMBLY_v1.md
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from engine.context.blocks import build_block, BLOCK_REGISTRY

logger = logging.getLogger(__name__)


class ContextAssembler:
    """Shared context assembly service. One instance per SIM run.

    Usage:
        assembler = ContextAssembler(sim_run_id, template_id)
        ctx = assembler.build(["sim_rules", "methodology", "world_state", "round_outputs"])
    """

    def __init__(
        self,
        sim_run_id: str,
        template_id: str = "default",
        *,
        countries: dict[str, dict] | None = None,
        world_state: dict | None = None,
        round_results: dict | None = None,
        sim_config: dict[str, str] | None = None,
        event_log: list[dict] | None = None,
        roles: dict[str, dict] | None = None,
    ):
        """Initialize with run context.

        For engine-internal use (no DB), pass data directly.
        For API use, data is loaded from Supabase on demand.

        Args:
            sim_run_id: Active SIM run identifier.
            template_id: Parent template (for methodology lookup).
            countries: Pre-loaded country dicts (engine format).
            world_state: Pre-loaded world state dict.
            round_results: This round's Pass 1 output.
            sim_config: Pre-loaded methodology entries {key: content}.
            event_log: Round-by-round events.
            roles: Role definitions {role_id: role_dict}.
        """
        self.sim_run_id = sim_run_id
        self.template_id = template_id

        # Data sources (can be set directly or loaded from DB)
        self._countries = countries
        self._world_state = world_state
        self._round_results = round_results
        self._sim_config = sim_config or {}
        self._event_log = event_log or []
        self._roles = roles or {}

        # Cache for built blocks
        self._cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, blocks: list[str], **params) -> str:
        """Assemble named blocks into a single context string.

        Args:
            blocks: List of block names, optionally scoped.
                    e.g., ["sim_rules", "world_state:columbia", "methodology"]
            **params: Additional parameters (round_num, role_id, etc.)

        Returns:
            Concatenated context string with section headers.
        """
        sections = []
        for block_spec in blocks:
            # Parse "block_name:scope" format
            parts = block_spec.split(":", 1)
            block_name = parts[0]
            scope = parts[1] if len(parts) > 1 else None

            content = self.get_block(block_name, scope=scope, **params)
            if content:
                sections.append(content)

        return "\n\n---\n\n".join(sections)

    def get_block(self, name: str, *, scope: str | None = None, **params) -> str:
        """Get a single context block. Uses cache when available.

        Args:
            name: Block name from BLOCK_REGISTRY.
            scope: Optional scope (e.g., country_id for visibility filtering).
            **params: Additional build parameters.

        Returns:
            Built block content string.
        """
        cache_key = f"{name}:{scope}" if scope else name
        if cache_key in self._cache:
            return self._cache[cache_key]

        if name not in BLOCK_REGISTRY:
            logger.warning("Unknown context block: %s", name)
            return ""

        content = build_block(name, self, scope=scope, **params)
        self._cache[cache_key] = content
        return content

    def invalidate(self, block_name: str | None = None):
        """Invalidate cache. None = invalidate all."""
        if block_name is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache if k.startswith(block_name)]
            for k in keys_to_remove:
                del self._cache[k]

    def get_methodology(self, key: str) -> str:
        """Shortcut: get a methodology entry."""
        return self._sim_config.get(key, "")

    def set_data(
        self,
        *,
        countries: dict | None = None,
        world_state: dict | None = None,
        round_results: dict | None = None,
        event_log: list | None = None,
    ):
        """Update data sources and invalidate affected caches."""
        if countries is not None:
            self._countries = countries
            self.invalidate("world_state")
        if world_state is not None:
            self._world_state = world_state
            self.invalidate("world_state")
            self.invalidate("round_inputs")
        if round_results is not None:
            self._round_results = round_results
            self.invalidate("round_outputs")
        if event_log is not None:
            self._event_log = event_log
            self.invalidate("sim_history")

    # ------------------------------------------------------------------
    # Data accessors (for block builders)
    # ------------------------------------------------------------------

    @property
    def countries(self) -> dict[str, dict]:
        return self._countries or {}

    @property
    def world_state(self) -> dict:
        return self._world_state or {}

    @property
    def round_results(self) -> dict | None:
        return self._round_results

    @property
    def event_log(self) -> list[dict]:
        return self._event_log

    @property
    def roles(self) -> dict[str, dict]:
        return self._roles

    @property
    def sim_config(self) -> dict[str, str]:
        return self._sim_config
