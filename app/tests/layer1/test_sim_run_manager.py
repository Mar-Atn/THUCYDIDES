"""L1 — SimRunManager state machine transition validation."""

import pytest
from engine.services.sim_run_manager import VALID_TRANSITIONS, _validate_transition


class TestStateTransitions:
    """Verify state machine transition rules."""

    def test_setup_to_pre_start(self):
        _validate_transition("setup", "pre_start")  # Should not raise

    def test_setup_to_active_blocked(self):
        with pytest.raises(ValueError, match="Cannot transition"):
            _validate_transition("setup", "active")

    def test_pre_start_to_active(self):
        _validate_transition("pre_start", "active")

    def test_active_to_processing(self):
        _validate_transition("active", "processing")

    def test_active_to_paused(self):
        _validate_transition("active", "paused")

    def test_processing_to_inter_round(self):
        _validate_transition("processing", "inter_round")

    def test_inter_round_to_active(self):
        _validate_transition("inter_round", "active")

    def test_paused_to_active(self):
        _validate_transition("paused", "active")

    def test_completed_cannot_transition(self):
        with pytest.raises(ValueError):
            _validate_transition("completed", "active")

    def test_aborted_cannot_transition(self):
        with pytest.raises(ValueError):
            _validate_transition("aborted", "active")

    def test_cannot_skip_phases(self):
        with pytest.raises(ValueError):
            _validate_transition("setup", "processing")

    def test_cannot_go_backward_without_explicit_method(self):
        with pytest.raises(ValueError):
            _validate_transition("processing", "setup")

    @pytest.mark.parametrize("status", VALID_TRANSITIONS.keys())
    def test_all_statuses_can_abort(self, status):
        if status in ("completed", "aborted"):
            return  # Terminal states
        _validate_transition(status, "aborted")

    def test_full_round_lifecycle(self):
        """Verify a complete round flows through all valid transitions."""
        transitions = [
            ("setup", "pre_start"),
            ("pre_start", "active"),       # Start sim → Phase A
            ("active", "processing"),       # End Phase A → Phase B
            ("processing", "inter_round"),  # End Phase B → Inter-round
            ("inter_round", "active"),      # Next round → Phase A
            ("active", "paused"),           # Pause
            ("paused", "active"),           # Resume
            ("active", "processing"),       # End Phase A again
            ("processing", "inter_round"),  # Phase B done
        ]
        for current, new in transitions:
            _validate_transition(current, new)  # Should not raise
