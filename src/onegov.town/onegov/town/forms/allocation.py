import sedate

from datetime import datetime, timedelta
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from onegov.form import Form, with_options
from onegov.form.fields import MultiCheckboxField, MultiCheckboxWidget
from onegov.form.parser.core import FieldDependency
from onegov.town import _
from onegov.town import utils
from wtforms.fields import RadioField, TextField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import TextInput
from wtforms_components import If


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

        return datetime.combine(d, utils.as_time(t))


class AllocationForm(Form, AllocationFormHelpers):
    """ Baseform for all allocation forms. Allocation forms are expected
    to implement the methods above (which contain a NotImplementedException).

    Have a look at :meth:`libres.db.scheduler.Scheduler.allocate` to find out
    more about those values.

    """

    start = DateField(_("Start"), [InputRequired()])
    end = DateField(_("End"), [InputRequired()])

    except_for = MultiCheckboxField(
        _("Except for"),
        choices=WEEKDAYS,
        widget=with_options(
            MultiCheckboxWidget,
            prefix_label=False,
            class_='oneline-checkboxes'
        )
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

    date = DateField(_("Date"), [InputRequired()])


class DaypassAllocationForm(AllocationForm):

    daypasses = IntegerField(_("Daypasses"), [InputRequired()])
    daypasses_limit = IntegerField(_("Daypasses Limit"), [InputRequired()])

    whole_day = True
    data = None

    @property
    def dates(self):
        return self.generate_dates(
            self.start.data,
            self.end.data,
            weekdays=self.weekdays
        )

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data


class DaypassAllocationEditForm(AllocationEditForm):

    daypasses = IntegerField(_("Daypasses"), [InputRequired()])
    daypasses_limit = IntegerField(_("Daypasses Limit"), [InputRequired()])

    whole_day = True
    data = None

    @property
    def dates(self):
        return (
            sedate.as_datetime(self.date.data),
            sedate.as_datetime(self.date.data) + timedelta(
                days=1, microseconds=-1
            )
        )

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data

    def apply_dates(self, start, end):
        self.date.data = start.date()

    def apply_model(self, model):
        self.date.data = model.display_start().date()
        self.daypasses.data = model.quota
        self.daypasses_limit.data = model.quota_limit


class RoomAllocationForm(AllocationForm):

    as_whole_day = RadioField(_("Whole day"), choices=[
        ('yes', _("Yes")),
        ('no', _("No"))
    ], default='yes')

    as_whole_day_dependency = FieldDependency('as_whole_day', 'no')

    start_time = TextField(
        label=_("Each starting at"),
        description=_("HH:MM"),
        validators=[If(as_whole_day_dependency.fulfilled, DataRequired())],
        widget=with_options(TextInput, **as_whole_day_dependency.html_data)
    )

    end_time = TextField(
        label=_("Each ending at"),
        description=_("HH:MM"),
        validators=[If(as_whole_day_dependency.fulfilled, DataRequired())],
        widget=with_options(TextInput, **as_whole_day_dependency.html_data)
    )

    data = None
    quota = 1
    quota_limit = 1

    @property
    def whole_day(self):
        return self.as_whole_day.data == 'yes'

    @property
    def dates(self):
        return self.generate_dates(
            self.start.data,
            self.end.data,
            utils.as_time(self.start_time.data),
            utils.as_time(self.end_time.data),
            self.weekdays
        )


class RoomAllocationEditForm(AllocationEditForm):

    as_whole_day = RadioField(_("Whole day"), choices=[
        ('yes', _("Yes")),
        ('no', _("No"))
    ], default='yes')

    as_whole_day_dependency = FieldDependency('as_whole_day', 'no')

    start_time = TextField(
        label=_("From"),
        description=_("HH:MM"),
        validators=[If(as_whole_day_dependency.fulfilled, DataRequired())],
        widget=with_options(TextInput, **as_whole_day_dependency.html_data)
    )

    end_time = TextField(
        label=_("Until"),
        description=_("HH:MM"),
        validators=[If(as_whole_day_dependency.fulfilled, DataRequired())],
        widget=with_options(TextInput, **as_whole_day_dependency.html_data)
    )

    data = None
    quota = 1
    quota_limit = 1

    @property
    def whole_day(self):
        return self.as_whole_day.data == 'yes'

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
        self.start_time.data = '{:%H:%M}'.format(start)
        self.end_time.data = '{:%H:%M}'.format(end)

    def apply_model(self, model):
        self.apply_dates(model.display_start(), model.display_end())
        self.as_whole_day.data = model.whole_day and 'yes' or 'no'
