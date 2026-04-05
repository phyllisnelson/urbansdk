from datetime import time

PERIODS: dict[int, tuple[str, time, time]] = {
    1: ("Overnight", time(0, 0), time(3, 59, 59)),
    2: ("Early Morning", time(4, 0), time(6, 59, 59)),
    3: ("AM Peak", time(7, 0), time(9, 59, 59)),
    4: ("Midday", time(10, 0), time(12, 59, 59)),
    5: ("Early Afternoon", time(13, 0), time(15, 59, 59)),
    6: ("PM Peak", time(16, 0), time(18, 59, 59)),
    7: ("Evening", time(19, 0), time(23, 59, 59)),
}

PERIOD_NAME_TO_ID: dict[str, int] = {name.lower(): pid for pid, (name, _, _) in PERIODS.items()}

DAYS: dict[str, int] = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}
