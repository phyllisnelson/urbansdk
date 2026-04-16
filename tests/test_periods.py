from datetime import time

import pytest

from app.enums import DayEnum, PeriodEnum


def test_period_enum_times():
    start, end = PeriodEnum.am_peak.times
    assert start == time(7, 0)
    assert end == time(9, 59, 59)


def test_period_enum_rejects_invalid():
    with pytest.raises(ValueError):
        PeriodEnum("Rush Hour")


def test_day_enum_iso_weekday():
    assert DayEnum.monday.iso_weekday == 1
    assert DayEnum.sunday.iso_weekday == 7


def test_day_enum_rejects_invalid():
    with pytest.raises(ValueError):
        DayEnum("Funday")
