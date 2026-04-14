"""Auth data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuthUser(BaseModel):
    """Authenticated user extracted from JWT + users table."""

    id: str
    email: str
    display_name: str
    system_role: str  # 'moderator' or 'participant'
    status: str  # 'registered', 'pending_approval', 'active', 'suspended'
    data_consent: bool = False

    @property
    def is_moderator(self) -> bool:
        return self.system_role == "moderator" and self.status == "active"

    @property
    def is_active(self) -> bool:
        return self.status in ("registered", "active")
