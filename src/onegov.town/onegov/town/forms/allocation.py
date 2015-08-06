import sedate

from datetime import datetime, time
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from onegov.form import Form, with_options
from onegov.form.parser.core import FieldDependency
from onegov.form.fields import MultiCheckboxField
from onegov.town import _
from wtforms.validators import DataRequired, InputRequired
from wtforms.fields import RadioField, TextField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.widgets import TextInput
from wtforms_components import If


WEEKDAYS = (
    (MO.weekday, _("Monday")),
    (TU.weekday, _("Tuesday")),
    (WE.weekday, _("Wednesday")),
    (TH.weekday, _("Thursday")),
    (FR.weekday, _("Friday")),
    (SA.weekday, _("Saturday")),
    (SU.weekday, _("Sunday")),
)


def choices_as_integer(choices):
    if choices is None:
        return None

    return [int(c) for c in choices]


class AllocationForm(Form):
    """ Baseform for all allocation forms. Allocation forms are expected
    to implement the methods above (which contain a NotImplementedException).

    Have a look at :meth:`libres.db.scheduler.Scheduler.allocate` to find out
    more about those values.

    """

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

    def generate_dates(self, start, end, start_time=None, end_time=None):
        """ Takes the given dates and generates the date tuples using rrule.
        The `except_for` field will be considered if present.

        """

        if start and end:
            start = sedate.as_datetime(start)
            end = sedate.as_datetime(end)

        if start == end:
            dates = (start, )
        else:
            if hasattr(self, 'except_for'):
                exceptions = {
                    int(x) for x in (self.except_for.data or tuple())
                }
                weekdays = [d[0] for d in WEEKDAYS if d[0] not in exceptions]

            dates = rrule(DAILY, dtstart=start, until=end, byweekday=weekdays)

        if start_time is None or end_time is None:
            return [(d, d) for d in dates]
        else:
            return [
                (
                    datetime.combine(d, start_time),
                    datetime.combine(d, end_time)
                ) for d in dates
            ]


class DaypassAllocationForm(AllocationForm):

    start = DateField(_("Start"), [InputRequired()])
    end = DateField(_("End"), [InputRequired()])

    daypasses = IntegerField(_("Daypasses"), [InputRequired()])
    daypasses_limit = IntegerField(_("Daypasses Limit"), [InputRequired()])

    except_for = MultiCheckboxField(
        _("Except for"),
        choices=WEEKDAYS,
        filters=[choices_as_integer]
    )

    whole_day = True
    data = None

    @property
    def dates(self):
        return self.generate_dates(self.start.data, self.end.data)

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data


class RoomAllocationForm(AllocationForm):

    start = DateField(_("Start"), [InputRequired()])
    end = DateField(_("End"), [InputRequired()])

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

    except_for = MultiCheckboxField(
        _("Except for"),
        choices=WEEKDAYS,
        filters=[choices_as_integer]
    )

    data = None
    quota = 1
    quota_limit = 1

    def as_time(self, text):
        return time(*(int(s) for s in text.split(':'))) if text else None

    def combine_datetime(self, field):
        d, t = (
            getattr(self, field).data,
            getattr(self, field + '_time').data
        )

        if d and not t:
            return sedate.as_datetime(d)

        if not t:
            return None

        return datetime.combine(d, self.as_time(t))

    @property
    def whole_day(self):
        return self.as_whole_day.data == 'yes'

    @property
    def dates(self):
        return self.generate_dates(
            self.combine_datetime('start'),
            self.combine_datetime('end'),
            self.as_time(self.start_time.data),
            self.as_time(self.end_time.data)
        )
