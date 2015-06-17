from datetime import datetime
from delorean import Delorean
from onegov.core.layout import Layout


def test_chunks():
    layout = Layout(model=object(), request=object())
    assert list(layout.chunks('ABCDEFG', 3, 'x')) == [
        ('A', 'B', 'C'),
        ('D', 'E', 'F'),
        ('G', 'x', 'x')
    ]


def test_format_date():
    layout = Layout(model=object(), request=object())

    dt = Delorean(
        datetime=datetime(2015, 6, 17, 12, 0), timezone='Europe/Zurich'
    ).datetime

    assert layout.format_date(dt, 'datetime') == '17.06.2015 12:00'
    assert layout.format_date(dt, 'date') == '17.06.2015'
    assert layout.format_date(dt.date(), 'date') == '17.06.2015'
    assert layout.format_date(dt, 'time') == '12:00'
    assert layout.format_date(dt.time(), 'time') == '12:00'
