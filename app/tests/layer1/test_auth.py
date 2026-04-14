"""Layer 1 tests for auth module — models and dependency logic."""

import pytest
from engine.auth.models import AuthUser


class TestAuthUser:
    """Test AuthUser model properties."""

    def test_active_moderator(self):
        user = AuthUser(
            id="abc",
            email="mod@test.com",
            display_name="Mod",
            system_role="moderator",
            status="active",
            data_consent=True,
        )
        assert user.is_moderator is True
        assert user.is_active is True

    def test_pending_moderator_not_moderator(self):
        """Pending moderator should NOT have moderator privileges."""
        user = AuthUser(
            id="abc",
            email="mod@test.com",
            display_name="Mod",
            system_role="moderator",
            status="pending_approval",
            data_consent=True,
        )
        assert user.is_moderator is False
        assert user.is_active is False

    def test_participant_not_moderator(self):
        user = AuthUser(
            id="abc",
            email="p@test.com",
            display_name="Player",
            system_role="participant",
            status="active",
            data_consent=True,
        )
        assert user.is_moderator is False
        assert user.is_active is True

    def test_suspended_user_not_active(self):
        user = AuthUser(
            id="abc",
            email="p@test.com",
            display_name="Player",
            system_role="participant",
            status="suspended",
            data_consent=True,
        )
        assert user.is_active is False
        assert user.is_moderator is False

    def test_registered_user_is_active(self):
        user = AuthUser(
            id="abc",
            email="p@test.com",
            display_name="Player",
            system_role="participant",
            status="registered",
            data_consent=False,
        )
        assert user.is_active is True

    @pytest.mark.parametrize(
        "role,status,expected_mod,expected_active",
        [
            ("moderator", "active", True, True),
            ("moderator", "pending_approval", False, False),
            ("moderator", "suspended", False, False),
            ("participant", "registered", False, True),
            ("participant", "active", False, True),
            ("participant", "suspended", False, False),
        ],
    )
    def test_role_status_matrix(self, role, status, expected_mod, expected_active):
        user = AuthUser(
            id="x",
            email="x@test.com",
            display_name="X",
            system_role=role,
            status=status,
        )
        assert user.is_moderator is expected_mod
        assert user.is_active is expected_active
