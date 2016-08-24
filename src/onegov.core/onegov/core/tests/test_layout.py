from datetime import date, datetime, timedelta
from sedate import replace_timezone, utcnow
from onegov.core.layout import Layout
from onegov.core.utils import Bunch


def test_chunks():
    layout = Layout(model=object(), request=object())
    assert list(layout.chunks('ABCDEFG', 3, 'x')) == [
        ('A', 'B', 'C'),
        ('D', 'E', 'F'),
        ('G', 'x', 'x')
    ]


def test_format_date():
    layout = Layout(model=object(), request=Bunch())

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


def test_format_number():

    layout = Layout(model=object(), request=Bunch())

    layout.request.locale = 'de_CH'
    assert layout.format_number(100) == "100"
    assert layout.format_number(100, 2) == "100.00"
    assert layout.format_number(1000) == "1'000"
    assert layout.format_number(1000.00) == "1'000.00"
    assert layout.format_number(1000.00, 0) == "1'000"

    layout.request.locale = 'de'
    assert layout.format_number(100) == "100"
    assert layout.format_number(100, 2) == "100,00"
    assert layout.format_number(1000) == "1.000"
    assert layout.format_number(1000.00) == "1.000,00"
    assert layout.format_number(1000.00, 0) == "1.000"


def test_relative_date():
    layout = Layout(model=object(), request=Bunch(locale='en'))
    text = layout.format_date(utcnow() - timedelta(seconds=60 * 5), 'relative')
    assert text == '5 minutes ago'
