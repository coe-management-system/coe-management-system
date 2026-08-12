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
    "low": 1,
    "normal": 2,
    "high": 3,
    "urgent": 4,
}


def get_priority_value(priority):
    """
    Convert a priority name into its numeric scheduling value.

    Args:
        priority: Priority name such as low, normal, high, or urgent.
                  Priority matching is case-insensitive.

    Returns:
        Integer priority value from 1 to 4.

    Raises:
        ValueError: If the supplied priority is not supported.

    Examples:
        get_priority_value("low") -> 1
        get_priority_value("normal") -> 2
        get_priority_value("high") -> 3
        get_priority_value("urgent") -> 4
    """
    priority = priority.lower()

    if priority not in PRIORITY_LEVELS:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Expected one of: {', '.join(PRIORITY_LEVELS.keys())}"
        )

    return PRIORITY_LEVELS[priority]