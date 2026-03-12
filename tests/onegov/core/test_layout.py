from __future__ import annotations

from datetime import date, datetime, timedelta
from sedate import replace_timezone, utcnow
from onegov.core.layout import Layout
from onegov.core.utils import Bunch


def test_batched() -> None:
    layout = Layout(
        model=object(),
        request=Bunch(app=Bunch(version='1.0', sentry_dsn=None))  # type: ignore[arg-type]
    )
    assert list(layout.batched('ABCDEFG', 3)) == [
        ('A', 'B', 'C'),
        ('D', 'E', 'F'),
        ('G',)
    ]


def test_format_date() -> None:
    layout = Layout(
        model=object(),
        request=Bunch(app=Bunch(version='1.0', sentry_dsn=None))  # type: ignore[arg-type]
    )

    dt = replace_timezone(datetime(2015, 6, 17, 15, 0), 'Europe/Zurich')

    layout.request.locale = 'de_CH'
    assert layout.format_date(dt, 'datetime') == '17.06.2015 15:00'
    assert layout.format_date(dt, 'datetime_long') == '17. Juni 2015 15:00'
    assert layout.format_date(dt, 'date') == '17.06.2015'
    assert layout.format_date(dt, 'date_long') == '17. Juni 2015'
    assert layout.format_date(dt, 'weekday_long') == 'Mittwoch'
    assert layout.format_date(dt, 'month_long') == 'Juni'
    assert layout.format_date(dt.date(), 'date') == '17.06.2015'
    assert layout.format_date(dt, 'time') == '15:00'
    assert layout.format_date(dt, 'time') == '15:00'
    assert layout.format_date(date(2016, 1, 3), 'date') == '03.01.2016'
    assert layout.format_date(None, 'datetime') == ''

    layout.day_long_format = 'skeleton:MMMMd'  # type: ignore[attr-defined]
    assert layout.format_date(dt, 'day_long') == '17. Juni'


def test_format_number() -> None:
    layout = Layout(
        model=object(),
        request=Bunch(app=Bunch(version='1.0', sentry_dsn=None))  # type: ignore[arg-type]
    )

    layout.request.locale = 'de_CH'
    assert layout.format_number(100) == "100"
    assert layout.format_number(100, 2) == "100.00"
    assert layout.format_number(10, 2, 6) == " 10.00"
    assert layout.format_number(10, 2, '06') == "010.00"
    assert layout.format_number(10, padding=3) == " 10"
    assert layout.format_number(10, padding='03') == "010"
    assert layout.format_number(1000) == "1’000"
    assert layout.format_number(1000, 2, 10) == "  1’000.00"
    assert layout.format_number(1000, 2, '010') == "001’000.00"
    assert layout.format_number(1000.00) == "1’000.00"
    assert layout.format_number(1000.00, 0) == "1’000"
    assert layout.format_number(1.1, 2, '05') == "01.10"
    assert layout.format_number(None) == ""

    layout.request.locale = 'de'
    assert layout.format_number(100) == "100"
    assert layout.format_number(100, 2) == "100,00"
    assert layout.format_number(10, 2, 6) == " 10,00"
    assert layout.format_number(10, 2, '06') == "010,00"
    assert layout.format_number(10, padding=3) == " 10"
    assert layout.format_number(10, padding='03') == "010"
    assert layout.format_number(1000) == "1.000"
    assert layout.format_number(1000, 2, 10) == "  1.000,00"
    assert layout.format_number(1000, 2, '010') == "001.000,00"
    assert layout.format_number(1000.00) == "1.000,00"
    assert layout.format_number(1000.00, 0) == "1.000"
    assert layout.format_number(1.1, 2, '05') == "01,10"
    assert layout.format_number(None) == ""


def test_relative_date() -> None:
    layout = Layout(
        model=object(),
        request=Bunch(locale='en', app=Bunch(version='1.0', sentry_dsn=None))  # type: ignore[arg-type]
    )
    text = layout.format_date(utcnow() - timedelta(seconds=60 * 5), 'relative')
    assert text == '5 minutes ago'
