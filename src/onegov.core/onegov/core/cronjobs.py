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


# a job that takes longer than this (seconds) will be reported
CRONJOB_MAX_DURATION = 30


# defines a valid cronjob format
CRONJOB_FORMAT = re.compile(r'\*/[0-9]+')


def parse_cron(value, type):
    """ Minimal cron style interval parser. Currently only supports this:

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
        return range(0, size)

    if value.isdigit():
        return (int(value), )

    if not isinstance(value, str):
        raise RuntimeError(f"Unexpected type for {value}: {type(value)}")

    if not CRONJOB_FORMAT.match(value):
        raise RuntimeError(f"{value} did not match {CRONJOB_FORMAT}")

    remainder = int(value.split('/')[-1])

    if remainder > size:
        raise RuntimeError(f"The remainder in {value} is too big")

    return (v for v in range(0, size) if v % remainder == 0)


class Job(object):
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

    def __init__(self, function, hour, minute, timezone, once=False, url=None):
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

        # pick an offset
        self.offset = Random(seed).randint(0, max_offset_seconds * prec) / prec

    @property
    def title(self):
        if not self.url:
            return self.name

        return self.url.split('://', maxsplit=1)[-1]

    def runtimes(self, today):
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

    def next_runtime(self, today=None):
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

        raise RuntimeError(f"Could not find a new runtime for job {self.name}")

    @property
    def id(self):
        """ Internal id signed by the application. Used to access the job
        through an url which must be unguessable, but the same over many
        processes.

        The signature is only possible if ``self.app`` is present, which
        can only be set after the instance has already been created.

        See :meth:`as_request_call`.

        """
        return quote_plus(self.app.sign(self.name))

    def as_request_call(self, request):
        """ Returns a new job which does the same as the old job, but it does
        so by calling an url which will execute the original job.

        """

        self.app = request.app
        url = request.link(self)

        def execute():
            # use curl for this because urllib randomly hangs if we use threads
            # (it's fine with processes). The requests library has the same
            # problem because it uses urllib internally. My guess is there's a
            # race condition between code listening for new connections and
            # urllib. In any case, using pycurl gets rid of this problem
            # without introducing a rather expensive subprocess.
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.setopt(pycurl.WRITEFUNCTION, lambda bytes: len(bytes))
            c.perform()
            c.close()

        return self.__class__(
            function=execute,
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

    def __init__(self, request, jobs):
        Thread.__init__(self, daemon=True)
        self.application_id = request.app.application_id
        self.jobs = tuple(job.as_request_call(request) for job in jobs)
        self.scheduler = sched.scheduler(timefunc=time.time)

        for job in self.jobs:
            job.next_runtime()

    def run(self):
        # the lock ensures that only one thread per application id is
        # in charge of running the scheduled jobs. If another thread already
        # has the lock, this thread will end immediately and be GC'd.
        with suppress(AlreadyLockedError):
            with local_lock('cronjobs-thread', self.application_id):
                log.info(f"Started cronjob thread for {self.application_id}")
                self.run_locked()

    def run_locked(self):
        for job in self.jobs:
            log.info(f"Enabled {job.title}")
            self.schedule(job)

        self.scheduler.run()

    def schedule(self, job):
        self.scheduler.enterabs(
            action=self.process_job,
            argument=(job, ),
            time=job.next_runtime().timestamp(),
            priority=0)

    def process_job(self, job):
        log.info(f"Executing {job.title}")

        try:
            start = datetime.utcnow()
            job.function()
            duration = (datetime.utcnow() - start).total_seconds()

            if duration > CRONJOB_MAX_DURATION:
                log.warn(f"{job.title} took too long ({duration})s")
            else:
                log.info(f"{job.title} finished in {duration}s")

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
def get_job(app, id):
    """ The internal path to the cronjob. The id can't be guessed. """
    name = app.unsign(unquote_plus(id))

    if name:
        return getattr(app.config.cronjob_registry, 'cronjobs', {}).get(name)


@Framework.view(model=Job, permission=Public)
def run_job(self, request):
    """ Executes the job. """
    self.function(request)


def register_cronjob(registry, function, hour, minute, timezone, once=False):

    # raises an error if the result cannot be parsed
    tuple(parse_cron(hour, 'hour'))
    tuple(parse_cron(minute, 'minute'))

    if not hasattr(registry, 'cronjobs'):
        registry.cronjobs = {}
        registry.cronjob_threads = {}

    job = Job(function, hour, minute, timezone, once=once)
    registry.cronjobs[job.name] = job
