"""Pure reminder detection logic for the Todo application.

This module contains the check_user() function that detects todos needing
reminder notifications or overdue notifications. It is a pure function with
no I/O and no side effects — it takes a list of todo dicts and the current
time, and returns notification records.

Stories covered: US-1 (backend portion), US-3, US-4
"""

from datetime import datetime, timezone
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications that can be triggered."""

    REMINDER_DUE = "reminder_due"
    OVERDUE = "overdue"


class Notification:
    """A notification record produced by the reminder checker.

    Attributes:
        todo_id: The ID of the todo that triggered this notification.
        todo_title: The title of the todo for display purposes.
        notification_type: Whether this is a reminder or overdue notification.
        triggered_at: When the notification was detected.
        due_date: The todo's due date (if any).
        reminder_at: The todo's reminder_at datetime (if any).
    """

    def __init__(
        self,
        todo_id: str,
        todo_title: str,
        notification_type: NotificationType,
        triggered_at: datetime,
        due_date: str | None = None,
        reminder_at: str | None = None,
    ):
        self.todo_id = todo_id
        self.todo_title = todo_title
        self.notification_type = notification_type
        self.triggered_at = triggered_at
        self.due_date = due_date
        self.reminder_at = reminder_at

    def to_dict(self) -> dict:
        """Serialize notification to a dictionary."""
        return {
            "todo_id": self.todo_id,
            "todo_title": self.todo_title,
            "notification_type": self.notification_type.value,
            "triggered_at": self.triggered_at.isoformat(),
            "due_date": self.due_date,
            "reminder_at": self.reminder_at,
        }


def check_user(
    todos: list[dict],
    now: datetime | None = None,
    already_notified: set[str] | None = None,
) -> list[Notification]:
    """Detect todos needing reminder or overdue notifications.

    This is a pure function — no I/O, no side effects. It examines a list
    of todo records and determines which ones should trigger notifications
    based on their reminder_at and due_date fields relative to the current time.

    Deduplication: If a todo_id is in the already_notified set, it will not
    produce a duplicate notification of the same type.

    Args:
        todos: List of todo dicts (as stored in the JSON store).
            Expected fields: id, title, status, due_date, reminder_at.
        now: The current datetime (UTC). Defaults to datetime.now(UTC) if None.
        already_notified: Set of "todo_id:notification_type" strings that have
            already been sent, used for deduplication.

    Returns:
        A list of Notification objects for todos that need notifications.

    Examples:
        >>> from datetime import datetime, timezone
        >>> todos = [
        ...     {"id": "1", "title": "Buy milk", "status": "pending",
        ...      "due_date": "2025-01-10", "reminder_at": "2025-01-09T09:00:00"},
        ... ]
        >>> now = datetime(2025, 1, 9, 10, 0, 0, tzinfo=timezone.utc)
        >>> results = check_user(todos, now=now)
        >>> len(results)
        1
        >>> results[0].notification_type
        <NotificationType.REMINDER_DUE: 'reminder_due'>
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if already_notified is None:
        already_notified = set()

    notifications: list[Notification] = []

    for todo in todos:
        todo_id = todo.get("id", "")
        todo_title = todo.get("title", "")
        status = todo.get("status", "")
        due_date_str = todo.get("due_date")
        reminder_at_str = todo.get("reminder_at")

        # Skip completed todos — no notifications needed
        if status == "done":
            continue

        # Check 1: reminder_at has passed → REMINDER_DUE notification
        if reminder_at_str:
            dedup_key = f"{todo_id}:{NotificationType.REMINDER_DUE.value}"
            if dedup_key not in already_notified:
                reminder_dt = _parse_datetime(reminder_at_str)
                if reminder_dt is not None and reminder_dt <= now:
                    notifications.append(
                        Notification(
                            todo_id=todo_id,
                            todo_title=todo_title,
                            notification_type=NotificationType.REMINDER_DUE,
                            triggered_at=now,
                            due_date=due_date_str,
                            reminder_at=reminder_at_str,
                        )
                    )

        # Check 2: due_date has passed → OVERDUE notification
        if due_date_str:
            dedup_key = f"{todo_id}:{NotificationType.OVERDUE.value}"
            if dedup_key not in already_notified:
                due_dt = _parse_date_as_datetime(due_date_str)
                if due_dt is not None and due_dt < now:
                    notifications.append(
                        Notification(
                            todo_id=todo_id,
                            todo_title=todo_title,
                            notification_type=NotificationType.OVERDUE,
                            triggered_at=now,
                            due_date=due_date_str,
                            reminder_at=reminder_at_str,
                        )
                    )

    return notifications


def _parse_datetime(value: str) -> datetime | None:
    """Parse an ISO 8601 datetime string, returning None on failure.

    Handles both timezone-aware and naive datetimes. Naive datetimes
    are assumed to be UTC.

    Args:
        value: ISO 8601 datetime string.

    Returns:
        Parsed datetime (UTC) or None if parsing fails.
    """
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _parse_date_as_datetime(value: str) -> datetime | None:
    """Parse a YYYY-MM-DD date string as a datetime at end-of-day UTC.

    A todo is overdue once the entire due date has passed, so we treat
    the due date as expiring at 23:59:59 UTC of that day.

    Args:
        value: Date string in YYYY-MM-DD format.

    Returns:
        Datetime at 23:59:59 UTC of the given date, or None if parsing fails.
    """
    try:
        from datetime import date as date_type

        d = date_type.fromisoformat(value)
        return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
