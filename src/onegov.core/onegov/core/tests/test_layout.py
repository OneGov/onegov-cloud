from datetime import datetime, timedelta
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
    layout = Layout(model=object(), request=object())

    dt = replace_timezone(datetime(2015, 6, 17, 12, 0), 'Europe/Zurich')

    assert layout.format_date(dt, 'datetime') == '17.06.2015 12:00'
    assert layout.format_date(dt, 'date') == '17.06.2015'
    assert layout.format_date(dt.date(), 'date') == '17.06.2015'
    assert layout.format_date(dt, 'time') == '12:00'
    assert layout.format_date(dt.time(), 'time') == '12:00'


def test_format_number():

    layout = Layout(model=object(), request=object())

    assert layout.format_number(100) == "100"
    assert layout.format_number(100, 2) == "100.00"
    assert layout.format_number(1000) == "1'000"
    assert layout.format_number(1000.00) == "1'000.00"
    assert layout.format_number(1000.00, 0) == "1'000"


def test_relative_date():
    layout = Layout(model=object(), request=Bunch(locale='en'))
    text = layout.format_date(utcnow() - timedelta(seconds=60 * 5), 'relative')
    assert text == '5 minutes ago'
