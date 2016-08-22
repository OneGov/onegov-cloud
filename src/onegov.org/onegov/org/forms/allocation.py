import sedate

from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from wtforms.fields import RadioField
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
        """ Takes the given dates and generates the date tuples using rrule.
        The `except_for` field will be considered if present.

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
            return [(d, d) for d in dates]
        else:
            if end_time < start_time:
                end_offset = timedelta(days=1)
            else:
                end_offset = timedelta()

            return [
                (
                    datetime.combine(d, start_time),
                    datetime.combine(d + end_offset, end_time)
                ) for d in dates
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

    @property
    def weekdays(self):
        """ The rrule weekdays derived from the except_for field. """
        exceptions = {x for x in (self.except_for.data or tuple())}
        return [int(d[0]) for d in WEEKDAYS if d[0] not in exceptions]

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
        fieldset=_("Date")
    )

    start_time = TimeField(
        label=_("Each starting at"),
        description=_("HH:MM"),
        validators=[InputRequired()],
        fieldset=_("Date"),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_("Each ending at"),
        description=_("HH:MM"),
        validators=[InputRequired()],
        fieldset=_("Date"),
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
        fieldset=_("Date")
    )

    start_time = TimeField(
        label=_("From"),
        description=_("HH:MM"),
        validators=[DataRequired()],
        fieldset=_("Date"),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_("Until"),
        description=_("HH:MM"),
        validators=[DataRequired()],
        fieldset=_("Date"),
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
