from datetime import timedelta

import pytest

from onegov.fsi.forms.course import datetime_to_string, \
    string_to_timedelta


@pytest.mark.parametrize("dt, string", [
    (timedelta(days=2 * 365), '2 years'),
    (timedelta(days=1), '1 day'),
    (timedelta(days=3), '3 days'),
    (timedelta(days=7), '1 week'),
    (timedelta(days=28), '4 weeks'),
    (timedelta(days=30), '1 month'),
    (timedelta(days=60), '2 months'),
    (timedelta(days=365), '1 year')
])
def test_datetime_string_conversion(dt, string):
    assert datetime_to_string(dt) == string
    assert string_to_timedelta(string) == dt


@pytest.mark.parametrize("dt, string", [
    (timedelta(days=2 * 365), '2 years'),
    (timedelta(days=1), ' 1.2 day '),
    (timedelta(days=3), '3days'),
    (timedelta(days=7), ' 1 week'),
    (timedelta(days=28), '4 weeks '),
    (timedelta(days=30), '1 month'),
    (timedelta(days=60), '2 months'),
    (timedelta(days=365), '1 year')

])
def test_string_to_timedelta(dt, string):
    assert string_to_timedelta(string) == dt
