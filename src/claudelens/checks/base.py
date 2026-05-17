"""Shared types for collision checks."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Finding:
    """A single collision finding."""

    check: str
    severity: Severity
    skills: tuple[str, ...]
    message: str
    score: float | None = None

    def sort_key(self):
        order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
        return (order[self.severity], self.check, self.skills)
