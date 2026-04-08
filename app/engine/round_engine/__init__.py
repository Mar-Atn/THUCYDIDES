"""Round resolution engine for the TTT Observatory.

Processes committed agent actions into world-state deltas each round:
combat, movement, mobilization, R&D, and logging.

Entry point: :func:`resolve_round.resolve_round`.
"""

from engine.round_engine.resolve_round import resolve_round

__all__ = ["resolve_round"]
