from __future__ import annotations

from datetime import date
from onegov.org.models.political_business import PoliticalBusiness
from sedate import as_datetime, replace_timezone


def _business(**kwargs: object) -> PoliticalBusiness:
    kwargs.setdefault('title', 'Budget 2021')
    kwargs.setdefault('political_business_type', 'motion')
    return PoliticalBusiness(**kwargs)


def test_fts_suggestion() -> None:
    business = _business()
    assert business.number is None
    assert business.fts_suggestion == ['Budget 2021']

    business.number = 'M-1'
    assert business.fts_suggestion == ['Budget 2021 M-1', 'M-1 Budget 2021']


def test_fts_last_change() -> None:
    business = _business()
    assert business.fts_last_change is None

    business.entry_date = date(2021, 5, 1)
    assert business.fts_last_change == replace_timezone(
        as_datetime(date(2021, 5, 1)), 'UTC')


def test_display_name() -> None:
    assert _business().display_name == 'Budget 2021'
    assert _business(number='M-1').display_name == 'M-1 Budget 2021'


def test_repr() -> None:
    text = repr(_business(number='M-1'))
    assert 'M-1' in text
    assert 'Budget 2021' in text
    assert 'motion' in text
