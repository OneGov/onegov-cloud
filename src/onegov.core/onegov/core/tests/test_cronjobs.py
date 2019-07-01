import requests

from datetime import datetime
from freezegun import freeze_time
from onegov.core import Framework
from onegov.core.cronjobs import parse_cron, Job
from onegov.core.utils import scan_morepath_modules
from pytest_localserver.http import WSGIServer
from sedate import replace_timezone
from sqlalchemy.ext.declarative import declarative_base
from time import sleep
from webtest import TestApp as Client


def test_run_cronjob(postgres_dsn, redis_url):
    result = 0

    class App(Framework):
        pass

    @App.path(path='')
    class Root(object):
        pass

    @App.json(model=Root)
    def view_root(self, request):
        return {}

    @App.cronjob(hour='*', minute='*', timezone='UTC', once=True)
    def run_test_cronjob(request):
        nonlocal result
        result += 1

    scan_morepath_modules(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=declarative_base(),
        redis_url=redis_url
    )
    app.namespace = 'municipalities'
    app.set_application_id('municipalities/new-york')

    # to test we need an actual webserver, webtest doesn't cut it here because
    # we are making requests from the application itself
    server = WSGIServer(application=app)

    try:
        server.start()

        with freeze_time(replace_timezone(datetime(2016, 1, 1, 8, 0), 'UTC')):
            requests.get(server.url)

            for i in range(0, 600):
                if result == 0:
                    sleep(0.1)
                else:
                    break

            sleep(0.1)
            assert result == 1

    finally:
        server.stop()


def test_disable_cronjobs(redis_url):

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
    app.configure_application(redis_url=redis_url)
    app.namespace = 'municipalities'
    app.set_application_id('municipalities/new-york')

    client = Client(app)
    client.get('/')

    assert not app.config.cronjob_registry.cronjob_threads


def test_parse_cron():
    assert tuple(parse_cron('*', 'hour')) == (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
        13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)

    assert tuple(parse_cron('*/2', 'hour')) == (
        0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)

    assert tuple(parse_cron('5', 'hour')) == (5, )
    assert tuple(parse_cron('*/20', 'minute')) == (0, 20, 40)


def test_job_offset():
    job = Job(test_job_offset, 8, 15, 'Europe/Zurich')
    assert job.offset != 0

    second_job = Job(test_job_offset, 8, 15, 'Europe/Zurich')
    assert second_job.offset == job.offset

    third_job = Job(lambda x: x, 8, 15, 'Europe/Zurich')
    assert third_job.offset != job.offset


def test_next_runtime():

    def in_timezone(*args, timezone='Europe/Zurich'):
        return replace_timezone(datetime(*args), timezone)

    def next_runtime(hour, minute, timezone='Europe/Zurich'):
        job = Job(lambda x: x, hour=hour, minute=minute, timezone=timezone)

        # disable offset for tests
        job.offset = 0

        return job.next_runtime()

    # fixed hour, minute
    with freeze_time(in_timezone(2019, 1, 1, 8, 14, 59)):
        assert next_runtime(hour=8, minute=15) \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 0)):
        assert next_runtime(hour=8, minute=15) \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 1)):
        assert next_runtime(hour=8, minute=15) \
            == in_timezone(2019, 1, 2, 8, 15)

    # any hour, fixed minute
    with freeze_time(in_timezone(2019, 1, 1, 8, 14, 59)):
        assert next_runtime(hour='*', minute=15) \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 0)):
        assert next_runtime(hour='*', minute=15) \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 1)):
        assert next_runtime(hour='*', minute=15) \
            == in_timezone(2019, 1, 1, 9, 15)

    # fixed hour, any minute
    with freeze_time(in_timezone(2019, 1, 1, 8, 14, 59)):
        assert next_runtime(hour=8, minute='*') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 0)):
        assert next_runtime(hour=8, minute='*') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 1)):
        assert next_runtime(hour=8, minute='*') \
            == in_timezone(2019, 1, 1, 8, 16)

    # any hour, every 15 minutes
    with freeze_time(in_timezone(2019, 1, 1, 8, 14, 59)):
        assert next_runtime(hour='*', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 0)):
        assert next_runtime(hour='*', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 1)):
        assert next_runtime(hour='*', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 30)

    with freeze_time(in_timezone(2019, 1, 1, 8, 45, 0)):
        assert next_runtime(hour='*', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 45)

    with freeze_time(in_timezone(2019, 1, 1, 8, 45, 1)):
        assert next_runtime(hour='*', minute='*/15') \
            == in_timezone(2019, 1, 1, 9, 0)

    # every 2 hours, every 15 minutes
    with freeze_time(in_timezone(2019, 1, 1, 8, 14, 59)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 0)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 15)

    with freeze_time(in_timezone(2019, 1, 1, 8, 15, 1)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 30)

    with freeze_time(in_timezone(2019, 1, 1, 8, 45, 0)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 1, 8, 45)

    with freeze_time(in_timezone(2019, 1, 1, 8, 45, 1)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 1, 10, 0)

    with freeze_time(in_timezone(2019, 1, 1, 23, 59, 59)):
        assert next_runtime(hour='*/2', minute='*/15') \
            == in_timezone(2019, 1, 2, 0, 0)
