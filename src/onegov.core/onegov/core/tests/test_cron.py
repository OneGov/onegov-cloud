import pytest

from datetime import datetime
from onegov.core.cronjobs import Cronjobs
from sedate import ensure_timezone, replace_timezone


def test_is_scheduled_at():
    cronjobs = Cronjobs()
    cron = cronjobs.cron

    @cron(hour=8, minute=0, timezone='CET')
    def each_morning(foo, bar):
        pass

    assert len(cronjobs.jobs) == 1
    job = cronjobs.jobs[0]

    assert len(job.id) == 64
    assert job.hour == 8
    assert job.minute == 0
    assert job.timezone == ensure_timezone('CET')
    assert job.name == 'test_is_scheduled_at.<locals>.each_morning'

    # dates must be timezone aware
    assert job.is_scheduled_at(
        replace_timezone(datetime(2015, 1, 1, 8), 'CET'))

    # though we may also use this shortcut for the same thing
    assert job.is_scheduled_at(datetime(2015, 1, 1, 8), 'CET')

    # if there's no timezone we fail
    with pytest.raises(AssertionError):
        job.is_scheduled_at(datetime(2015, 1, 1, 8))

    assert not job.is_scheduled_at(datetime(2015, 1, 1, 7, 59), 'CET')
    assert job.is_scheduled_at(datetime(2015, 1, 1, 8, 0, 1), 'CET')
    assert job.is_scheduled_at(datetime(2015, 1, 1, 8, 0, 59), 'CET')
    assert not job.is_scheduled_at(datetime(2015, 1, 1, 8, 1), 'CET')

    assert not job.is_scheduled_at(datetime(2015, 1, 1, 8, 0, 1), 'UTC')
    assert not job.is_scheduled_at(datetime(2015, 1, 1, 8, 0, 59), 'UTC')
    assert job.is_scheduled_at(datetime(2015, 1, 1, 7, 0, 1), 'UTC')
    assert job.is_scheduled_at(datetime(2015, 1, 1, 7, 0, 59), 'UTC')
