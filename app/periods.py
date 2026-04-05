from datetime import time

from app.constants import DAYS, PERIOD_NAME_TO_ID, PERIODS


def resolve_period(period: str | int) -> tuple[time, time]:
    """Return (start, end) times for a period given by ID or name."""
    if isinstance(period, int) or (isinstance(period, str) and period.isdigit()):
        pid = int(period)
        if pid not in PERIODS:
            raise ValueError(f"Unknown period ID: {pid}. Valid IDs: 1-7")
        _, start, end = PERIODS[pid]
        return start, end

    pid = PERIOD_NAME_TO_ID.get(period.lower())
    if pid is None:
        raise ValueError(
            f"Unknown period name: '{period}'. Valid names: {list(PERIOD_NAME_TO_ID.keys())}"
        )
    _, start, end = PERIODS[pid]
    return start, end


def resolve_day(day: str) -> int:
    """Return ISO weekday (1=Monday … 7=Sunday) for a day name."""
    dow = DAYS.get(day.lower())
    if dow is None:
        raise ValueError(f"Unknown day: '{day}'. Valid days: {list(DAYS.keys())}")
    return dow
