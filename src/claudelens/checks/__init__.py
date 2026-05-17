"""Collision-detection checks."""
from claudelens.checks.base import Finding, Severity
from claudelens.checks.descriptions import check_descriptions
from claudelens.checks.naming import check_naming
from claudelens.checks.triggers import check_triggers

__all__ = [
    "Finding",
    "Severity",
    "check_descriptions",
    "check_naming",
    "check_triggers",
]
