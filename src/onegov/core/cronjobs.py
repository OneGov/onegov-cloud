""" Provides a way to specify cronjobs which should be called at an exact time.

Example::

    # A job that runs at 08:00 exactly
    @App.cronjob(hour=8, minute=0, timezone='Europe/Zurich')
    def cleanup_stuff(request):
        pass

    # A job that runs every 15 minutes
    @App.cronjob(hour='*', minute='*/15', timezone='UTC')
    def do_interesting_things(request):
        pass

Functions registered like this will be called through a regular request. That
means they are just like any other view and have all the power associated with
it.

Warnings
--------

The function is called *once* for *each* application id! So when the time
comes for your function to be called, you can expect many calls on a busy
site. Each application id also gets its own thread, which is not terribly
efficient. It is expected that this behaviour will change in the future
with an improved scheduling mechanism.

Also note that the scheduler will offset your function automatically by up
to 30 seconds, to mitigate against the trampling herd problem.

As a result you want to use this feature sparingly. If possible do clean up
on user action (either manually, or when the user changes something somewhat
related). For example, we clean up old reservation records whenever a new
reservation is received.

This also means that it is better to have a cronjob that runs once a day
on a specific time (say at 13:37 each day), than a cronjob that runs exactly
on 00:00 when a lot of other things might be scheduled.

Also the more a cronjob is called the costlier it is for the site (a job
that runs every minute is naturally more heavy on resources than one run
every 15 minutes).

Finally note that cronjobs for any given application id are only run once the
first request to the application with that id has been made. The reason for
this is the fact that the background thread needs a real request to be
initialized.

In other words, if nobody visits the website the cronjob runs on, then
the cronjobs won't run.

"""
from __future__ import annotations

import sched
import re
import time
import pycurl

from contextlib import suppress
from datetime import datetime, timedelta, date
from onegov.core.errors import AlreadyLockedError
from onegov.core.framework import Framework, log
from onegov.core.security import Public
from onegov.core.utils import local_lock
from random import Random
from sedate import ensure_timezone, replace_timezone, utcnow
from sentry_sdk import capture_exception
from threading import Thread
from urllib.parse import quote_plus, unquote_plus


from typing import Any, Generic, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from sedate.types import TzInfo, TzInfoOrName
    from typing import TypeAlias

    from .request import CoreRequest

    Scheduled: TypeAlias = Callable[[], Any]
    Executor: TypeAlias = Callable[[CoreRequest], Any]


_JobFunc = TypeVar('_JobFunc', 'Executor', 'Scheduled')


# a job that takes longer than this (seconds) will be reported
CRONJOB_MAX_DURATION = 30


# defines a valid cronjob format
CRONJOB_FORMAT = re.compile(r'\*/[0-9]+')


def parse_cron(
    value: str | int,
    type: Literal['hour', 'minute']
) -> Iterable[int]:
    """ Minimal cron style interval parser. Currently only supports this::

        *   -> Run every hour, minute
        */2 -> Run every other hour, minute
        2   -> Run on the given hour, minute

    Returns a tuple, iterator or generator.

    """

    if type == 'hour':
        size = 24
    elif type == 'minute':
        size = 60
    else:
        raise NotImplementedError()

    if isinstance(value, int):
        return (value, )

    if value == '*':
        return range(size)

    if value.isdigit():
        return (int(value), )

    if not isinstance(value, str):
        raise TypeError(f'Unexpected type for {value}: {type(value)}')

    if not CRONJOB_FORMAT.match(value):
        raise ValueError(f'{value} did not match {CRONJOB_FORMAT}')

    remainder = int(value.split('/')[-1])

    if remainder > size:
        raise ValueError(f'The remainder in {value} is too big')

    return (v for v in range(size) if v % remainder == 0)


class Job(Generic[_JobFunc]):
    """ A single cron job. """

    __slots__ = (
        'app',
        'name',
        'function',
        'hour',
        'minute',
        'timezone',
        'offset',
        'once',
        'url',
    )

    app: Framework
    name: str
    function: _JobFunc
    hour: int | str
    minute: int | str
    timezone: TzInfo
    offset: float
    once: bool
    url: str | None

    def __init__(
        self,
        function: _JobFunc,
        hour: int | str,
        minute: int | str,
        timezone: TzInfoOrName,
        once: bool = False,
        url: str | None = None
    ):
        # the name is used to make sure the job is only run by one process
        # at a time in multi process environment. It needs to be unique
        # for each process but the same in all processes.
        self.name = function.__qualname__

        self.function = function
        self.hour = hour
        self.minute = minute
        self.timezone = ensure_timezone(timezone)
        self.url = url
        self.once = once

        # avoid trampling herds with a predictable random number (i.e one that
        # stays the same between repeated restarts on the same platform)
        max_offset_seconds = 30

        # we need an offset in seconds, but calculate one in ms
        prec = 1000

        # use a predictable seed
        seed = self.url or self.name

        # FIXME: This is a bit odd, we pick an offset twice for each job, since
        #        we first create the job that will be run via a HTTP request
        #        and then the job that will run the first job via curl, so we
        #        compute an unecessary offset, we should probably separate
        #        this properly instead of making Job generic, so we have a
        #        ExecutorJob and a ScheduledJob, the offset is a concern of
        #        the scheduler and not of the job executor
        # pick an offset
        self.offset = Random(
            seed).randint(0, max_offset_seconds * prec) / prec  # nosec B311

    @property
    def title(self) -> str:
        if not self.url:
            return self.name

        return self.url.partition('://')[-1]

    def runtimes(self, today: date) -> Iterator[datetime]:
        """ Generates the runtimes of this job on the given day, excluding
        runtimes in the past.

        """
        now = utcnow()
        today = datetime(today.year, today.month, today.day)

        hours = parse_cron(self.hour, type='hour')

        # we need to loop over this multiple time, therefore put into a tuple
        minutes = tuple(parse_cron(self.minute, type='minute'))

        for hour in hours:
            for minute in minutes:
                runtime = today.replace(hour=hour, minute=minute)
                runtime = replace_timezone(runtime, self.timezone)
                runtime += timedelta(seconds=self.offset)

                if now <= runtime:
                    yield runtime

    def next_runtime(self, today: date | None = None) -> datetime:
        """ Returns the time (epoch) when this job should be run next, not
        taking into account scheduling concerns (like when it has run last).

        If no runtime is found for today, a runtime is searched tomorrow. If
        that doesn't work, no next runtime exists. This would be an error,
        since we do not currently support things like weekly cronjobs.

        """

        for runtime in self.runtimes(today or date.today()):
            return runtime

        if not today:
            return self.next_runtime(date.today() + timedelta(days=1))

        raise RuntimeError(f'Could not find a new runtime for job {self.name}')

    @property
    def id(self) -> str:
        """ Internal id signed by the application. Used to access the job
        through an url which must be unguessable, but the same over many
        processes.

        The signature is only possible if ``self.app`` is present, which
        can only be set after the instance has already been created.

        See :meth:`as_request_call`.

        """
        return quote_plus(self.app.sign(self.name, 'cronjob-id'))

    def as_request_call(self, request: CoreRequest) -> Job[Scheduled]:
        """ Returns a new job which does the same as the old job, but it does
        so by calling an url which will execute the original job.

        """

        self.app = request.app
        url = request.link(self)

        def execute() -> None:
            # use curl for this because urllib randomly hangs if we use threads
            # (it's fine with processes). The requests library has the same
            # problem because it uses urllib internally. My guess is there's a
            # race condition between code listening for new connections and
            # urllib. In any case, using pycurl gets rid of this problem
            # without introducing a rather expensive subprocess.
            c = pycurl.Curl()
            c.setopt(pycurl.URL, url)
            c.setopt(pycurl.WRITEFUNCTION, lambda bytes: len(bytes))
            c.perform()
            c.close()

        # NOTE: These type ignore are only necessary, because we tried to
        #       handle both things in one class
        return self.__class__(  # type: ignore[return-value]
            function=execute,  # type:ignore[arg-type]
            hour=self.hour,
            minute=self.minute,
            timezone=self.timezone,
            once=self.once,
            url=url)


class ApplicationBoundCronjobs(Thread):
    """ A daemon thread which runs the cronjobs it is given in the background.

    The cronjobs are not actually run in the same thread. Instead a request to
    the actual cronjob is made. This way the thread is pretty much limited to
    basic IO work (GET request) and the actual cronjob is called with a normal
    request.

    Basically there is no difference between calling the url of the cronjob
    at a scheduled time and using this cronjob.

    This also avoids any and all locking problems as we don't have to write
    OneGov applications in a thread safe way. The actual work is always done
    on the main thread.

    Each application id is meant to have its own thread. To avoid extra
    work we make sure that only one thread per application exists on each
    server. This is accomplished by holding a local lock during
    the lifetime of the thread.

    WARNING This doesn't work on distributed systems. That is if the onegov
    processes are distributed over many servers the lock isn't shared.

    This can be achieved, but it's difficult to get right, so for now we
    do not implement it, as we do not have distributed systems yet.

    """

    def __init__(
        self,
        request: CoreRequest,
        jobs: Iterable[Job[Executor]]
    ):
        Thread.__init__(self, daemon=True)
        self.application_id = request.app.application_id
        self.jobs = tuple(job.as_request_call(request) for job in jobs)
        self.scheduler = sched.scheduler(timefunc=time.time)

        for job in self.jobs:
            job.next_runtime()

    def run(self) -> None:
        # the lock ensures that only one thread per application id is
        # in charge of running the scheduled jobs. If another thread already
        # has the lock, this thread will end immediately and be GC'd.
        with (
            suppress(AlreadyLockedError),
            local_lock('cronjobs-thread', self.application_id)
        ):
            log.info(f'Started cronjob thread for {self.application_id}')
            self.run_locked()

    # FIXME: This should probably not be public API if it's only supposed
    #        to run in a locked state
    def run_locked(self) -> None:
        for job in self.jobs:
            log.info(f'Enabled {job.title}')
            self.schedule(job)

        self.scheduler.run()

    def schedule(self, job: Job[Scheduled]) -> None:
        self.scheduler.enterabs(
            action=self.process_job,
            argument=(job, ),
            time=job.next_runtime().timestamp(),
            priority=0)

    def process_job(self, job: Job[Scheduled]) -> None:
        log.info(f'Executing {job.title}')

        try:
            start = time.perf_counter()
            job.function()
            duration = time.perf_counter() - start

            if duration > CRONJOB_MAX_DURATION:
                log.warn(f'{job.title} took too long ({duration:.3f})s')
            else:
                log.info(f'{job.title} finished in {duration:.3f}s')

        except Exception as e:
            # exceptions in OneGov Cloud are captured mostly automatically, but
            # here this is different because we run off the main-thread and
            # are not part of the request/response cycle
            capture_exception(e)
        finally:
            # schedule the job again, even if there were errors

            if not job.once:
                self.schedule(job)


@Framework.path(model=Job, path='/cronjobs/{id}')
def get_job(app: Framework, id: str) -> Job[Executor] | None:
    """ The internal path to the cronjob. The id can't be guessed. """
    # FIXME: This should really use a dynamic salt, but we will have to
    #        be careful about race conditions between dispatch and
    #        execution. While these urls should be virtually unguessable
    #        if they leak through a log-file etc. they could be reused.
    #        Or we could do something similar to OCQMS and only allow
    #        local connections, although this may be difficult to ensure
    #        for all possible deployments.
    name = app.unsign(unquote_plus(id), 'cronjob-id')

    if name:
        return getattr(app.config.cronjob_registry, 'cronjobs', {}).get(name)
    return None


@Framework.view(model=Job, permission=Public)
def run_job(self: Job[Executor], request: CoreRequest) -> None:
    """ Executes the job. """
    self.function(request)


def register_cronjob(
    registry: object,
    function: Executor,
    hour: int | str,
    minute: int | str,
    timezone: TzInfoOrName,
    once: bool = False
) -> None:

    # raises an error if the result cannot be parsed
    tuple(parse_cron(hour, 'hour'))
    tuple(parse_cron(minute, 'minute'))

    if not hasattr(registry, 'cronjobs'):
        registry.cronjobs = {}  # type:ignore[attr-defined]
        registry.cronjob_threads = {}  # type:ignore[attr-defined]

    job = Job(function, hour, minute, timezone, once=once)
    registry.cronjobs[job.name] = job  # type:ignore[attr-defined]
