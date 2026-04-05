import pytest

from app.periods import resolve_day, resolve_period


def test_resolve_period_rejects_unknown_numeric_id():
    with pytest.raises(ValueError, match="Unknown period ID"):
        resolve_period(99)


def test_resolve_day_rejects_unknown_day():
    with pytest.raises(ValueError, match="Unknown day"):
        resolve_day("noday")
