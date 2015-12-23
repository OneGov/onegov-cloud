from datetime import datetime, time, timedelta
from functools import wraps
from onegov.core.crypto import random_token
from sedate import ensure_timezone, replace_timezone


class Cronjobs(object):
    """ A registry of cronjobs. Does not execute them, only keeps them. """

    def __init__(self):
        self.jobs = []

    def cron(self, hour, minute, timezone):
        """ Decorator which adds decorated functions to the jobs list.

        :hour:
            The hour this cronjob should be run in.

        :minute:
            The minute this cronjob should be run in.

        :timezone:
            The timezone to which hour and minute refer.

        More cron-like arguments (like hour='*/5') are *not yet implemented*,
        but they may be in the future by changing this function.

        """
        def decorator(fn):
            self.jobs.append(Job(fn, hour, minute, timezone))

            @wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            return wrapper

        return decorator


class Job(object):
    """ A single cron job. """

    def __init__(self, function, hour, minute, timezone):
        # the id is used to call the job as an anonymous user using an url
        # therefore it needs to be unguessable
        self.id = random_token()
        self.function = function
        self.hour = hour
        self.minute = minute
        self.timezone = ensure_timezone(timezone)

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
