"""
Scheduling priority classification.

This module provides a simple deterministic priority system for
scheduling decisions.

Supported priorities:

    low       -> 1
    normal    -> 2
    high      -> 3
    urgent    -> 4

Higher numeric values represent higher scheduling priority.

This prototype does not determine priorities automatically. The priority
must be supplied as part of the timetable event.
"""


PRIORITY_LEVELS = {
    "flexible": 1,
    "normal": 2,
    "high": 3,
    "critical": 4,
}

_PRIORITY_ALIASES = {
    "low": "flexible",
    "urgent": "critical",
}


def get_priority_value(priority):
    """
    Convert a priority name into its numeric scheduling value.

    Args:
        priority: Priority name such as flexible, normal, high, or critical.
                  Priority matching is case-insensitive. Legacy aliases
                  ``low`` and ``urgent`` are also accepted for backward
                  compatibility. Numeric priority values from 1 to 4 are
                  returned unchanged.

    Returns:
        Integer priority value from 1 to 4.

    Raises:
        ValueError: If the supplied priority is not supported.

    Examples:
        get_priority_value("flexible") -> 1
        get_priority_value("normal") -> 2
        get_priority_value("high") -> 3
        get_priority_value("critical") -> 4
        get_priority_value("low") -> 1
        get_priority_value("urgent") -> 4
        get_priority_value(3) -> 3
    """
    if isinstance(priority, int):
        if priority in PRIORITY_LEVELS.values():
            return priority
        raise ValueError(
            f"Invalid priority {priority}. "
            f"Expected one of: {', '.join(PRIORITY_LEVELS.keys())}"
        )

    normalized = priority.lower()

    if normalized in _PRIORITY_ALIASES:
        normalized = _PRIORITY_ALIASES[normalized]

    if normalized not in PRIORITY_LEVELS:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Expected one of: {', '.join(PRIORITY_LEVELS.keys())}"
        )

    return PRIORITY_LEVELS[normalized]