""" Provides a way to specify cronjobs which should be called at an exact time.

Example::

    @App.cronjob(hour=8, minute=0, timezone='Europe/Zurich')
    def cleanup_stuff(request):
        pass

Functions registered like this will be called through a regular request. That
means they are just like any other view and have all the power associated with
it.

WARNING: The function is called ONCE for EACH application id. So at the given
time there might be a number of calls more or less at the same time, run
against your function.

In terms of operations this means that there should be more processes than
application ids (tennants). In terms of development this means that you
should keep the time spent in a cronjob to an absolute minimum! Long running
jobs (more than 30 seconds) are reported.

This feature should really be used sparingly and only for things where the
exact time is relevant. Cleanup jobs for example should be combined with
delete/update/add jobs for example, not pushed off to a cronjob.

We also make sure that there's only one job each 5 minutes (at 00:00, 00:05,
and so on) and that there are no two jobs run at the same time.

For now cronjobs are furthermore limited to be run once a day. In the future
we might add a model more akin to classic cronjobs.

Finally note that cronjobs for any given application id are only run once the
first request to the application with that id has been made. The reason for
this is the fact that the background thread needs a real request to be
initialized.

"""

import pycurl

from contextlib import suppress
from datetime import datetime, time, timedelta
from onegov.core.framework import Framework, log
from onegov.core.locking import lock, AlreadyLockedError
from onegov.core.security import Public
from sedate import ensure_timezone, replace_timezone
from threading import Thread
from time import sleep
from urllib.parse import quote_plus, unquote_plus


# the number of seconds the cronjob thread waits between polls, 45 was chosen
# because it means that each thread is run at least once a minute
CRONJOB_POLL_RESOLUTION = 45

# a job that takes longer than this (seconds) will be reported
CRONJOB_MAX_DURATION = 30


class Job(object):
    """ A single cron job. """

    def __init__(self, function, hour, minute, timezone):
        # the name is used to make sure the job is only run by one process
        # at a time in multi process environment. It needs to be unqiue
        # for each process but the same in all processes.
        self.name = function.__qualname__

        self.function = function
        self.hour = hour
        self.minute = minute
        self.timezone = ensure_timezone(timezone)

    @property
    def id(self):
        """ Internal id signed by the application. Used to access the job
        through an url which must be unguessable, but the same over many
        processes.

        The signature is only possible if ``self.app`` is present, which
        can only be set after the instance has already been created.

        See :meth:`as_request_call`.

        """

        assert self.app
        return quote_plus(self.app.sign(self.name))

    def as_request_call(self, request):
        """ Returns a new job which does the same as the old job, but it does
        so by calling an url which will execute the original job.

        """

        self.app = request.app
        url = request.link(self)

        def execute():
            # use curl for this because the urllib randomly hangs if we
            # use threads (it's fine with procsesses). requests has the same
            # problem because it uses urllib internally. My guess is there's
            # a race condition between code listening for new connections
            # and urllib. In any case, using pycurl gets rid of this problem
            # without introducing a rather expensive subprocess.
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.setopt(pycurl.WRITEFUNCTION, lambda bytes: len(bytes))
            c.perform()
            c.close()

        return self.__class__(execute, self.hour, self.minute, self.timezone)

    def is_scheduled_at(self, point, timezone=None):
        """ Returns True if the job is scheduled to run at the given date.

        :point:
            The point in time. Needs to be a timezone aware datetime object,
            unless ``timezone`` is passed as well.

        :timezone:
            Optional. If the passed date is not timezone aware, the date is
            assumed to be from this timezone.

        :returns:
            True if the job is scheduled at this date. The maximum
            resolution is one minute. That means if the date given
            falls within the minute of the scheduled time it is assumed
            to be a match (i.e anywhere within 0' - 59'999.99999)

        """

        assert point.tzinfo or timezone
        point = point if point.tzinfo else replace_timezone(point, timezone)

        start = datetime.combine(point.date(), time(self.hour, self.minute))
        start = replace_timezone(start, self.timezone)

        return start <= point < (start + timedelta(minutes=1))


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
    server. This is accomplished by holding a postgres advisory lock during
    the lifetime of the thread.

    """

    def __init__(self, request, jobs, session_manager):
        Thread.__init__(self, daemon=True)
        self.application_id = request.app.application_id
        self.jobs = tuple(job.as_request_call(request) for job in jobs)
        self.session_manager = session_manager

        log.info("Starting Cronjob Thread for {}".format(self.application_id))

        for job in jobs:
            log.info(
                "Enabling Cronjob {} ({})".format(job.name, request.link(job))
            )

    def run(self):
        session = self.session_manager.session()
        previous_check = datetime.min

        # the lock ensures that only one thread per application id is
        # in charge of running the scheduled jobs. If another thread already
        # has the lock, this thread will end immediately and be GC'd.
        with suppress(AlreadyLockedError):
            with lock(session, 'cronjobs-thread', self.application_id):
                while not sleep(CRONJOB_POLL_RESOLUTION):

                    # make sure we only run the jobs once a minute (we poll
                    # for it more often than that because we are not
                    # guaranteed to run in precise intervals)
                    this_check = datetime.utcnow()

                    if this_check.date() == previous_check.date():
                        if this_check.hour == previous_check.hour:
                            if this_check.minute == previous_check.minute:
                                continue

                    previous_check = this_check
                    self.run_scheduled_jobs()

        # we need to close the session again or it will stay open forever
        session.close()

        log.info("Stopping Cronjob Thread for {}, already locked!".format(
            self.application_id
        ))

    def run_scheduled_jobs(self):
        point = replace_timezone(datetime.utcnow(), 'UTC')

        for job in self.jobs:
            if job.is_scheduled_at(point):

                start = datetime.utcnow()
                job.function()
                duration = (datetime.utcnow() - start).total_seconds()

                if duration > CRONJOB_MAX_DURATION:
                    log.warning(
                        "The job for {} at {}:{} took too long ({}s)".format(
                            self.application_id, job.hour, job.minute, duration
                        )
                    )


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


def register_cronjob(registry, function, hour, minute, timezone):
    assert minute % 5 == 0, "The cronjobs must be added in 5 minute increments"

    if not hasattr(registry, 'cronjobs'):
        registry.cronjobs = {}
        registry.cronjob_threads = {}

    job = Job(function, hour, minute, timezone)
    registry.cronjobs[job.name] = job
