"""Outbound notifications (stubbed)."""

from __future__ import annotations

from typing import List

from ..utils.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Sends notifications to users about task and project events."""

    def __init__(self) -> None:
        self.sent: List[str] = []

    def notify(self, user_id: int, message: str) -> None:
        """Record and 'send' a notification to a user.

        In production this would push to email/websocket; here we just log it
        so the call chain remains observable from tests.
        """
        entry = f"user={user_id}: {message}"
        self.sent.append(entry)
        logger.info("notify %s", entry)
