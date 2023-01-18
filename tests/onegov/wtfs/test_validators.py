from freezegun import freeze_time
from pytest import raises
from wtforms.validators import ValidationError
import babel.dates
from onegov.wtfs.forms.scan_job import DispatchTimeValidator
from datetime import datetime, timedelta
from sedate import replace_timezone
import pytz


def test_dispatch_date_validator():
    class Field:
        def __init__(self, _datetime):
            self.data = _datetime

    validator = DispatchTimeValidator(max_hour=17)

    still_ok_hour = validator.max_hour - 1
    valid_time = datetime(2023, 1, 1, still_ok_hour, 0)
    time = str(
        babel.dates.format_datetime(
            valid_time, format="yyyy-MM-dd HH:mm", locale="de_CH"
        )
    )

    with freeze_time(time):
        selected_dispatch_date = datetime(2023, 1, 1, still_ok_hour, 0).date()
        validator(None, Field(selected_dispatch_date))

        selected_dispatch_date = datetime(2023, 1, 2, 12, 0)
        validator(None, Field(selected_dispatch_date))

    invalid_time = valid_time + timedelta(hours=1)
    time = str(
        babel.dates.format_datetime(
            invalid_time, format="yyyy-MM-dd HH:mm", locale="de_CH"
        )
    )
    with freeze_time(time):
        max_hour = validator.max_hour
        with raises(ValidationError):
            # No scans for municipalities after max (inclusive)
            selected_dispatch_date = datetime(2023, 1, 1, max_hour, 50).date()
            validator(None, Field(selected_dispatch_date))


def test_comparing_date_by_days():
    def tzdatetime(year, month, day, hour, minute, timezone):
        return replace_timezone(
            datetime(year, month, day, hour, minute), timezone
        )

    tz = "Europe/Zurich"
    today: datetime = pytz.timezone(tz).localize(
        datetime(2023, 1, 1, hour=10, minute=0)
    )

    dispatch_date: datetime = tzdatetime(2023, 1, 1, 11, 0, tz)

    is_same_day = today.date() == dispatch_date.date()
    assert is_same_day

    dispatch_date = tzdatetime(2023, 1, 1, 1, 0, tz)
    is_same_day = today.date() == dispatch_date.date()
    assert is_same_day

    dispatch_date = tzdatetime(2023, 1, 1, 23, 59, tz)
    is_same_day = today.date() == dispatch_date.date()
    assert is_same_day

    dispatch_date = tzdatetime(2023, 1, 2, 0, 1, tz)
    is_same_day = today.date() == dispatch_date.date()
    assert not is_same_day
