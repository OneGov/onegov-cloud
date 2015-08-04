from datetime import datetime, time
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.libres.models import Resource
from onegov.town import _
from onegov.town.models.extensions import (
    HiddenFromPublicExtension,
    ContactExtension,
    PersonLinkExtension
)
from wtforms.validators import InputRequired
from wtforms.fields import TextField
from wtforms.fields.html5 import DateField, IntegerField


WEEKDAYS = (
    (MO.weekday, _("Monday")),
    (TU.weekday, _("Tuesday")),
    (WE.weekday, _("Wednesday")),
    (TH.weekday, _("Thursday")),
    (FR.weekday, _("Friday")),
    (SA.weekday, _("Saturday")),
    (SU.weekday, _("Sunday")),
)


class DaypassResource(Resource, HiddenFromPublicExtension,
                      ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}


class RoomResource(Resource, HiddenFromPublicExtension,
                   ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'room'}


class AllocationForm(Form):

    @property
    def dates(self):
        raise NotImplementedError

    @property
    def whole_day(self):
        raise NotImplementedError

    @property
    def quota(self):
        raise NotImplementedError

    @property
    def quota_limit(self):
        raise NotImplementedError

    @property
    def data(self):
        raise NotImplementedError


class DaypassAllocationForm(AllocationForm):

    start = DateField(_("Start"), [InputRequired])
    end = DateField(_("End"), [InputRequired])

    daypasses = IntegerField(_("Daypasses"), [InputRequired])
    daypasses_limit = IntegerField(_("Daypasses Limit"), [InputRequired])

    except_for = MultiCheckboxField(_("Except for"), choices=WEEKDAYS)

    whole_day = True
    data = None

    @property
    def dates(self):
        if self.start.data == self.end.data:
            return [(self.start.data, self.end.data)]
        else:
            exceptions = {int(x) for x in (self.except_for.data or tuple())}
            weekdays = [d[0] for d in WEEKDAYS if d[0] not in exceptions]

            dates = rrule(
                DAILY,
                dtstart=self.start.data,
                until=self.end.data,
                byweekday=weekdays
            )

            return [(d, d) for d in dates]

    @property
    def quota(self):
        return self.daypasses.data

    @property
    def quota_limit(self):
        return self.daypasses_limit.data


class RoomAllocationForm(AllocationForm):

    start_date = DateField(_("Start"), [InputRequired])
    end_date = DateField(_("End"), [InputRequired])

    start_time = TextField("Each starting at", [InputRequired])
    end_time = TextField("Each starting at", [InputRequired])

    except_for = MultiCheckboxField(_("Except for"), choices=WEEKDAYS)

    whole_day = False
    data = None
    quota = 1
    quota_limit = 1

    def as_time(self, text):
        return time(*(int(s) for s in text.split(':'))) if text else None

    def combine_datetime(self, prefix):
        d, t = (
            getattr(self, prefix + '_date').data,
            getattr(self, prefix + '_time').data
        )

        if not (d and t):
            return None

        return datetime.combine(d, self.as_time(t))

    @property
    def start(self):
        return self.combine_datetime('start')

    @property
    def end(self):
        return self.combine_datetime('end')

    @property
    def dates(self):
        if self.start_date.data == self.end_date.data:
            return [(self.start, self.end)]
        else:
            exceptions = {int(x) for x in (self.except_for.data or tuple())}
            weekdays = [d[0] for d in WEEKDAYS if d[0] not in exceptions]

            dates = rrule(
                DAILY,
                dtstart=self.start,
                until=self.end,
                byweekday=weekdays
            )

            start_time, end_time = (
                self.as_time(self.start_time.data),
                self.as_time(self.end_time.data)
            )

            return [
                (
                    datetime.combine(d, start_time),
                    datetime.combine(d, end_time)
                ) for d in dates
            ]
