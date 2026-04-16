from datetime import time
from enum import Enum


class PeriodEnum(str, Enum):
    def __new__(cls, label: str, start: time, end: time):
        obj = str.__new__(cls, label)
        obj._value_ = label
        obj.start = start
        obj.end = end
        return obj

    overnight = ("Overnight", time(0, 0), time(3, 59, 59))
    early_morning = ("Early Morning", time(4, 0), time(6, 59, 59))
    am_peak = ("AM Peak", time(7, 0), time(9, 59, 59))
    midday = ("Midday", time(10, 0), time(12, 59, 59))
    early_afternoon = ("Early Afternoon", time(13, 0), time(15, 59, 59))
    pm_peak = ("PM Peak", time(16, 0), time(18, 59, 59))
    evening = ("Evening", time(19, 0), time(23, 59, 59))

    @property
    def times(self) -> tuple[time, time]:
        return self.start, self.end


class DayEnum(str, Enum):
    def __new__(cls, label: str, weekday: int):
        obj = str.__new__(cls, label)
        obj._value_ = label
        obj.iso_weekday = weekday
        return obj

    monday = ("Monday", 1)
    tuesday = ("Tuesday", 2)
    wednesday = ("Wednesday", 3)
    thursday = ("Thursday", 4)
    friday = ("Friday", 5)
    saturday = ("Saturday", 6)
    sunday = ("Sunday", 7)
