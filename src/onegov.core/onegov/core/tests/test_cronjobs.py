import pytest
import requests

from datetime import datetime
from freezegun import freeze_time
from morepath.error import ConflictError
from onegov.core import cronjobs, Framework
from onegov.core.utils import scan_morepath_modules
from pytest_localserver.http import WSGIServer
from sedate import ensure_timezone, replace_timezone
from sqlalchemy.ext.declarative import declarative_base
from time import sleep
from webtest import TestApp as Client


def test_is_scheduled_at():
    job = cronjobs.Job(lambda: None, hour=8, minute=0, timezone='CET')

    assert job.hour == 8
    assert job.minute == 0
    assert job.timezone == ensure_timezone('CET')
    assert job.name == 'test_is_scheduled_at.<locals>.<lambda>'

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


def test_overlapping_cronjobs():

    class App(Framework):
        pass

    @App.cronjob(hour=8, minute=0, timezone='UTC')
    def first_job(request):
        pass

    @App.cronjob(hour=8, minute=0, timezone='UTC')
    def second_job(request):
        pass

    scan_morepath_modules(App)

    with pytest.raises(ConflictError):
        App.commit()


def test_non_5_minutes_cronjobs():

    class App(Framework):
        pass

    @App.cronjob(hour=8, minute=1, timezone='UTC')
    def first_job(request):
        pass

    scan_morepath_modules(App)

    with pytest.raises(AssertionError):
        App.commit()


def test_cronjobs_integration(postgres_dsn):

    result = 0
    cronjobs.CRONJOB_POLL_RESOLUTION = 1

    class App(Framework):
        pass

    @App.path(path='')
    class Root(object):
        pass

    @App.json(model=Root)
    def view_root(self, request):
        return {}

    @App.cronjob(hour=8, minute=0, timezone='UTC')
    def run_test_cronjob(request):
        nonlocal result
        result += 1

    scan_morepath_modules(App)

    app = App()
    app.configure_application(dsn=postgres_dsn, base=declarative_base())
    app.namespace = 'municipalities'
    app.set_application_id('municipalities/new-york')

    # to test we need an actual webserver, webtest doesn't cut it here because
    # we are making requests from the application itself
    server = WSGIServer(application=app)

    try:
        server.start()

        with freeze_time(replace_timezone(datetime(2016, 1, 1, 8, 0), 'UTC')):
            requests.get(server.url)
            sleep(2.5)

    finally:
        server.stop()

    assert result == 1


def test_disable_cronjobs():

    class App(Framework):
        pass

    @App.path(path='')
    class Root(object):
        pass

    @App.json(model=Root)
    def view_root(self, request):
        return {}

    @App.cronjob(hour=8, minute=0, timezone='UTC')
    def run_test_cronjob(request):
        pass

    @App.setting(section='cronjobs', name='enabled')
    def cronjobs_enabled():
        return False

    scan_morepath_modules(App)

    app = App()
    app.configure_application()
    app.namespace = 'municipalities'
    app.set_application_id('municipalities/new-york')

    client = Client(app)
    client.get('/')

    assert not app.config.cronjob_registry.cronjob_threads
