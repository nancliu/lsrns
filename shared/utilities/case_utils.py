"""
Case utility functions for case type detection and management.
"""

from typing import Optional


def is_event_based_case(case_id: str) -> bool:
    """
    Check if case is event-based.

    Args:
        case_id: The case ID to check

    Returns:
        True if case is event-based, False otherwise

    Examples:
        >>> is_event_based_case("case_event_10814")
        True
        >>> is_event_based_case("case_20251114_170211")
        False
    """
    return case_id.startswith("case_event_")


def get_event_id_from_case(case_id: str) -> Optional[str]:
    """
    Extract event ID from case ID.

    Args:
        case_id: The case ID to extract event ID from

    Returns:
        The event ID if case is event-based, None otherwise

    Examples:
        >>> get_event_id_from_case("case_event_10814")
        '10814'
        >>> get_event_id_from_case("case_20251114_170211")
        None
    """
    if is_event_based_case(case_id):
        return case_id.replace("case_event_", "")
    return None


def get_case_type(case_id: str) -> str:
    """
    Get case type: 'event_based' or 'time_based'.

    Args:
        case_id: The case ID to check

    Returns:
        'event_based' if case follows event-based pattern, 'time_based' otherwise

    Examples:
        >>> get_case_type("case_event_10814")
        'event_based'
        >>> get_case_type("case_20251114_170211")
        'time_based'
    """
    return "event_based" if is_event_based_case(case_id) else "time_based"
