import sedate

from cached_property import cached_property
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from uuid import uuid4
from wtforms.fields import StringField, RadioField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import DataRequired, NumberRange, InputRequired
from wtforms_components import TimeField


WEEKDAYS = (
    (str(MO.weekday), _("Mo")),
    (str(TU.weekday), _("Tu")),
    (str(WE.weekday), _("We")),
    (str(TH.weekday), _("Th")),
    (str(FR.weekday), _("Fr")),
    (str(SA.weekday), _("Sa")),
    (str(SU.weekday), _("Su")),
)


def choices_as_integer(choices):
    if choices is None:
        return None

    return [int(c) for c in choices]


class AllocationFormHelpers(object):

    def generate_dates(self, start, end,
                       start_time=None, end_time=None, weekdays=None):
        """ Takes the given dates and generates the date tuples.

        The ``except_for`` field will be considered if present, as will the
        ``on_holidays`` setting.

        """

        if not (start and end):
            return []

        start = start and sedate.as_datetime(start)
        end = end and sedate.as_datetime(end)

        if start == end:
            dates = (start, )
        else:
            dates = rrule(DAILY, dtstart=start, until=end, byweekday=weekdays)

        if start_time is None or end_time is None:
            return [(d, d) for d in dates if not self.is_excluded(d)]
        else:
            if end_time < start_time:
                end_offset = timedelta(days=1)
            else:
                end_offset = timedelta()

            return [
                (
                    datetime.combine(d, start_time),
                    datetime.combine(d + end_offset, end_time)
                ) for d in dates if not self.is_excluded(d)
            ]

    def combine_datetime(self, field, time_field):
        """ Takes the given date field and combines it with the given time
        field. """

        d, t = getattr(self, field).data, getattr(self, time_field).data

        if d and not t:
            return sedate.as_datetime(d)

        if not t:
            return None

        return datetime.combine(d, t)

    def is_excluded(self, date):
        return False


class AllocationRuleForm(Form):
    """ Base form form allocation rules. """

    title = StringField(
        label=_("Title"),
        description=_("General availability"),
        validators=[InputRequired()],
        fieldset=_("Rule"))

    extend = RadioField(
        label=_("Extend"),
        validators=[InputRequired()],
        fieldset=_("Rule"),
        default='daily',
        choices=(
            ('daily', _("Extend by one day at midnight")),
            ('monthly', _("Extend by one month at the end of the month")),
            ('yearly', _("Extend by one year at the end of the year"))
        ))

    @cached_property
    def rule_id(self):
        return uuid4().hex

    @cached_property
    def iteration(self):
        return 0

    @cached_property
    def last_run(self):
        None

    @property
    def rule(self):
        return {
            'id': self.rule_id,
            'title': self.title.data,
            'extend': self.extend.data,
            'options': self.options,
            'iteration': self.iteration,
            'last_run': self.last_run,
        }

    @rule.setter
    def rule(self, value):
        self.__dict__['rule_id'] = value['id']
        self.__dict__['iteration'] = value['iteration']
        self.__dict__['last_run'] = value['last_run']

        self.title.data = value['title']
        self.extend.data = value['extend']

        for k, v in value['options'].items():
            if hasattr(self, k):
                getattr(self, k).data = v

    @property
    def options(self):
        return {
            k: getattr(self, k).data for k in self._fields
            if k not in ('title', 'extend', 'csrf_token')
        }

    def apply(self, resource):
        if self.iteration == 0:
            dates = self.dates
        else:
            unit = {
                'daily': 'days',
                'monthly': 'months',
                'yearly': 'years'
            }[self.extend.data]

            start = self.end.data + timedelta(days=1)
            end = self.end.data + relativedelta(**{unit: self.iteration})

            if hasattr(self, 'start_time'):
                start_time = self.start_time.data
                end_time = self.end_time.data
            else:
                start_time = None
                end_time = None

            dates = self.generate_dates(
                start,
                end,
                start_time=start_time,
                end_time=end_time,
                weekdays=self.weekdays
            )

        data = {**(self.data or {}), 'rule': self.rule_id}

        return len(resource.scheduler.allocate(
            dates=dates,
            whole_day=self.whole_day,
            quota=self.quota,
            quota_limit=self.quota_limit,
            data=data,
            partly_available=self.partly_available,
            skip_overlapping=True
        ))


class AllocationForm(Form, AllocationFormHelpers):
    """ Baseform for all allocation forms. Allocation forms are expected
    to implement the methods above (which contain a NotImplementedException).

    Have a look at :meth:`libres.db.scheduler.Scheduler.allocate` to find out
    more about those values.

    """

    start = DateField(
        label=_("Start"),
        validators=[InputRequired()],
        fieldset=_("Date")
    )

    end = DateField(
        label=_("End"),
        validators=[InputRequired()],
        fieldset=_("Date")
    )

    except_for = MultiCheckboxField(
        label=_("Except for"),
        choices=WEEKDAYS,
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        },
        fieldset=("Date")
    )

    on_holidays = RadioField(
        label=_("On holidays"),
        choices=(
            ('yes', _("Yes")),
            ('no', _("No"))
        ),
        default='yes',
        fieldset=_("Date"))

    def on_request(self):
        if not self.request.app.org.holidays:
            self.delete_field('on_holidays')

    def ensure_start_before_end(self):
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                self.start.errors.append(_("Start date before end date"))
                return False

    @property
    def weekdays(self):
        """ The rrule weekdays derived from the except_for field. """
        exceptions = {x for x in (self.except_for.data or tuple())}
        return [int(d[0]) for d in WEEKDAYS if d[0] not in exceptions]

    @cached_property
    def exceptions(self):
        if not hasattr(self, 'request'):
            return ()

        if not self.on_holidays:
            return ()

        if self.on_holidays.data == 'yes':
            return ()

        return self.request.app.org.holidays

    def is_excluded(self, date):
        return date.date() in self.exceptions

    @property
    def dates(self):
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def whole_day(self):
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def partly_available(self):
        """  Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def quota(self):
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def quota_limit(self):
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def data(self):
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError


class AllocationEditForm(Form, AllocationFormHelpers):
    """ Baseform for edit forms. Edit forms differ from the base allocation
    form somewhat, since they don't offer a way to generate more than
    one allocation at a time.

    The dates property is therefore expected to return a single start, end
    dates tuple.

    """

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        fieldset=_("Date")
    )


class Daypasses(object):

    daypasses = IntegerField(
        label=_("Daypasses"),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_("Daypasses")
    )

    daypasses_limit = IntegerField(
        label=_("Daypasses Limit"),
        validators=[
            InputRequired(),
            NumberRange(0, 999)
        ],
        fieldset=_("Daypasses")
    )


class DaypassAllocationForm(AllocationForm, Daypasses):

    whole_day = True
    partly_available = False
    data = None

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data

    @property
    def dates(self):
        return self.generate_dates(
            self.start.data,
            self.end.data,
            weekdays=self.weekdays
        )


class DaypassAllocationEditForm(AllocationEditForm, Daypasses):

    whole_day = True
    partly_available = False
    data = None

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data

    @property
    def dates(self):
        return (
            sedate.as_datetime(self.date.data),
            sedate.as_datetime(self.date.data) + timedelta(
                days=1, microseconds=-1
            )
        )

    def apply_dates(self, start, end):
        self.date.data = start.date()

    def apply_model(self, model):
        self.date.data = model.display_start().date()
        self.daypasses.data = model.quota
        self.daypasses_limit.data = model.quota_limit


class RoomAllocationForm(AllocationForm):

    as_whole_day = RadioField(
        label=_("Whole day"),
        choices=[
            ('yes', _("Yes")),
            ('no', _("No"))
        ],
        default='yes',
        fieldset=_("Time")
    )

    start_time = TimeField(
        label=_("Each starting at"),
        description=_("HH:MM"),
        validators=[InputRequired()],
        fieldset=_("Time"),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_("Each ending at"),
        description=_("HH:MM"),
        validators=[InputRequired()],
        fieldset=_("Time"),
        depends_on=('as_whole_day', 'no')
    )

    is_partly_available = RadioField(
        label=_("May be partially reserved"),
        choices=[
            ('yes', _("Yes")),
            ('no', _("No"))
        ],
        default='yes',
        fieldset=_("Options")
    )

    data = None
    quota = 1
    quota_limit = 1

    @property
    def whole_day(self):
        return self.as_whole_day.data == 'yes'

    @property
    def partly_available(self):
        return self.is_partly_available.data == 'yes'

    @property
    def dates(self):
        return self.generate_dates(
            self.start.data,
            self.end.data,
            self.start_time.data,
            self.end_time.data,
            self.weekdays
        )


class RoomAllocationEditForm(AllocationEditForm):

    as_whole_day = RadioField(
        label=_("Whole day"),
        choices=[
            ('yes', _("Yes")),
            ('no', _("No"))
        ],
        default='yes',
        fieldset=_("Time")
    )

    start_time = TimeField(
        label=_("From"),
        description=_("HH:MM"),
        validators=[DataRequired()],
        fieldset=_("Time"),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_("Until"),
        description=_("HH:MM"),
        validators=[DataRequired()],
        fieldset=_("Time"),
        depends_on=('as_whole_day', 'no')
    )

    data = None
    quota = 1
    quota_limit = 1

    @property
    def whole_day(self):
        return self.as_whole_day.data == 'yes'

    @property
    def partly_available(self):
        return self.is_partly_available.data == 'yes'

    @property
    def dates(self):
        if self.whole_day:
            return (
                sedate.as_datetime(self.date.data),
                sedate.as_datetime(self.date.data) + timedelta(
                    days=1, microseconds=-1
                )
            )
        else:
            return (
                self.combine_datetime('date', 'start_time'),
                self.combine_datetime('date', 'end_time'),
            )

    def apply_dates(self, start, end):
        self.date.data = start.date()
        self.start_time.data = start.time()
        self.end_time.data = end.time()

    def apply_model(self, model):
        self.apply_dates(model.display_start(), model.display_end())
        self.as_whole_day.data = model.whole_day and 'yes' or 'no'
