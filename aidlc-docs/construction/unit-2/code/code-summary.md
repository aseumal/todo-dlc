# Code Summary — Unit 2: Reminder Trigger Logic

## Overview

Unit 2 extends the Todo application with reminder trigger detection logic. It adds a `reminder_at` field to the Todo model and creates a pure function (`check_user`) that detects todos needing reminder or overdue notifications.

## Stories Covered

- **US-1** (backend portion) — Todo reminder scheduling
- **US-3** — Reminder trigger detection
- **US-4** — Overdue todo detection

## Files Modified

### 1. `backend/models.py`

**Changes:**
- Added `reminder_at: datetime | None = None` to the `Todo` model — stores the ISO 8601 datetime when a reminder should trigger
- Added `reminder_at: str | None = None` to `TodoCreate` — accepts ISO 8601 datetime string on creation
- Added `reminder_at: str | None = None` to `TodoUpdate` — accepts ISO 8601 datetime string on update, explicit empty string clears the field

### 2. `backend/services/todo_service.py`

**Changes:**
- Added `_validate_reminder_at(self, reminder_at: str) -> datetime` — validates ISO 8601 datetime format, returns parsed datetime or raises `ValidationError`
- Updated `create()` — accepts `reminder_at` from `TodoCreate`, validates format, persists ISO string to store
- Updated `update()` — accepts `reminder_at` from `TodoUpdate`, validates format, supports clearing via explicit empty string `""`

## Files Created

### 3. `backend/reminder_checker.py`

**Purpose:** Pure function module with no I/O and no side effects.

**Key Components:**
- `NotificationType` enum — `REMINDER_DUE`, `OVERDUE`
- `Notification` class — data object representing a triggered notification
- `check_user(todos, now, already_notified)` — main detection function

**Logic:**
1. Iterates over all todos for a user
2. Skips todos with `status == "done"`
3. Checks if `reminder_at` datetime has passed → produces `REMINDER_DUE` notification
4. Checks if `due_date` has fully passed (end of day UTC) → produces `OVERDUE` notification
5. Deduplicates using `already_notified` set with keys formatted as `"{todo_id}:{notification_type}"`

**Design Decisions:**
- Pure function: takes data in, returns results out — no database calls, no file I/O
- Deduplication is caller-managed via the `already_notified` parameter
- Naive datetimes are assumed UTC
- Due dates expire at 23:59:59 UTC (a todo is overdue only after the full day passes)

## Validation Rules

| Field | Format | Example |
|-------|--------|---------|
| `reminder_at` | ISO 8601 datetime | `2025-06-15T09:00:00` |
| `due_date` | ISO 8601 date | `2025-06-15` |

## Contract Compliance

All function signatures match the inception contract specifications:
- `check_user(todos: list[dict], now: datetime | None, already_notified: set[str] | None) -> list[Notification]`
- `_validate_reminder_at(self, reminder_at: str) -> datetime`
- `TodoCreate.reminder_at: str | None`
- `TodoUpdate.reminder_at: str | None`
- `Todo.reminder_at: datetime | None`

## Syntax Validation

All Python files pass syntax validation (`python -c "import ast; ast.parse(open(f).read())"` succeeds for all modified/created files).
