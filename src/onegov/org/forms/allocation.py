from __future__ import annotations

import sedate

from functools import cached_property
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY
from uuid import uuid4
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import DataRequired, NumberRange, InputRequired

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import TimeField
from onegov.form.filters import as_float
from onegov.org import _
from onegov.org.forms.util import WEEKDAYS


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from onegov.org.request import OrgRequest
    from onegov.reservation import Allocation, Resource
    from onegov.core.types import SequenceOrScalar
    from typing import Protocol

    class DateContainer(Protocol):
        def __contains__(self, dt: date | datetime, /) -> bool: ...


def choices_as_integer(choices: Iterable[str] | None) -> list[int] | None:
    if choices is None:
        return None

    return [int(c) for c in choices]


class AllocationFormHelpers:

    def generate_dates(
        self,
        start: date | None,
        end: date | None,
        start_time: time | None = None,
        end_time: time | None = None,
        weekdays: Iterable[int] | None = None
    ) -> list[tuple[datetime, datetime]]:
        """ Takes the given dates and generates the date tuples.

        The ``except_for`` field will be considered if present, as will the
        ``on_holidays`` setting.

        """

        if not (start and end):
            return []

        start_dt = sedate.as_datetime(start)
        end_dt = sedate.as_datetime(end)

        dates: Iterable[datetime]
        if start_dt == end_dt:
            dates = (start_dt, )
        else:
            dates = rrule(
                DAILY,
                dtstart=start_dt,
                until=end_dt,
                byweekday=weekdays
            )

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

    def combine_datetime(self, field: str, time_field: str) -> datetime | None:
        """ Takes the given date field and combines it with the given time
        field. """

        d, t = getattr(self, field).data, getattr(self, time_field).data

        if d and not t:
            return sedate.as_datetime(d)

        if not t:
            return None

        return datetime.combine(d, t)

    def is_excluded(self, dt: datetime) -> bool:
        return False


class AllocationRuleForm(Form):
    """ Base form form allocation rules. """

    if TYPE_CHECKING:
        # forward declare required properties/methods
        @property
        def dates(self) -> SequenceOrScalar[tuple[datetime, datetime]]: ...
        @property
        def weekdays(self) -> Iterable[int]: ...
        @property
        def whole_day(self) -> bool: ...
        @property
        def quota(self) -> int: ...
        @property
        def quota_limit(self) -> int: ...
        @property
        def partly_available(self) -> bool: ...

        def generate_dates(
            self,
            start: date | None,
            end: date | None,
            start_time: time | None = None,
            end_time: time | None = None,
            weekdays: Iterable[int] | None = None
        ) -> Sequence[tuple[datetime, datetime]]: ...

    title = StringField(
        label=_('Title'),
        description=_('General availability'),
        validators=[InputRequired()],
        fieldset=_('Period'))

    extend = RadioField(
        label=_('Extend'),
        validators=[InputRequired()],
        fieldset=_('Period'),
        default='no',
        choices=(
            ('no', _("Don't extend this availability period automatically")),
            ('daily', _('Extend by one day at midnight')),
            ('monthly', _('Extend by one month at the end of the month')),
            ('yearly', _('Extend by one year at the end of the year'))
        ))

    @cached_property
    def rule_id(self) -> str:
        return uuid4().hex

    @cached_property
    def iteration(self) -> int:
        return 0

    @cached_property
    def last_run(self) -> datetime | None:
        return None

    @property
    def rule(self) -> dict[str, Any]:
        return {
            'id': self.rule_id,
            'title': self.title.data,
            'extend': self.extend.data,
            'options': self.options,
            'iteration': self.iteration,
            'last_run': self.last_run,
        }

    @rule.setter
    def rule(self, value: dict[str, Any]) -> None:
        # this is a little scary, maybe these shouldn't be
        # cached properties and instead just attributes that
        # get generated and pre-filled inside __init__
        self.__dict__['rule_id'] = value['id']
        self.__dict__['iteration'] = value['iteration']
        self.__dict__['last_run'] = value['last_run']

        self.title.data = value['title']
        self.extend.data = value['extend']

        for k, v in value['options'].items():
            if k in self:
                self[k].data = v

    @property
    def options(self) -> dict[str, Any]:
        return {
            k: f.data for k, f in self._fields.items()
            if k not in ('title', 'extend', 'csrf_token')
        }

    def apply(self, resource: Resource) -> int:
        if self.iteration == 0:
            dates = self.dates
        else:
            match self.extend.data:
                case 'daily':
                    end_offset = relativedelta(days=self.iteration)
                case 'monthly':
                    end_offset = relativedelta(months=self.iteration)
                case 'yearly':
                    end_offset = relativedelta(years=self.iteration)
                case _:
                    raise AssertionError('unreachable')

            start = self['end'].data + timedelta(days=1)
            end = self['end'].data + end_offset

            if 'start_time' in self:
                start_time = self['start_time'].data
                end_time = self['end_time'].data
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

    if TYPE_CHECKING:
        request: OrgRequest

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        fieldset=_('Date')
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()],
        fieldset=_('Date')
    )

    except_for = MultiCheckboxField(
        label=_('Except for'),
        choices=WEEKDAYS,
        coerce=int,
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        },
        fieldset=('Date')
    )

    on_holidays = RadioField(
        label=_('On holidays'),
        choices=(
            ('yes', _('Yes')),
            ('no', _('No'))
        ),
        default='yes',
        fieldset=_('Date'))

    during_school_holidays = RadioField(
        label=_('During school holidays'),
        choices=(
            ('yes', _('Yes')),
            ('no', _('No'))
        ),
        default='yes',
        fieldset=_('Date'))

    pricing_method = RadioField(
        label=_('Price'),
        fieldset=_('Payments'),
        default='inherit',
        validators=[InputRequired()],
        choices=(
            ('inherit', _('Inherit from resource')),
            ('free', _('Free of charge')),
            ('per_item', _('Per item')),
            ('per_hour', _('Per hour'))
        )
    )

    price_per_item = DecimalField(
        label=_('Price per item'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_item')
    )

    price_per_hour = DecimalField(
        label=_('Price per hour'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_hour')
    )

    # NOTE: Having a currency field is a little bit suspect, since we can't
    #       really mix currencies currently anyways. But eventually we might
    #       need it, so let's just add it now, even if it may cause some
    #       issues in the mean time.
    currency = StringField(
        label=_('Currency'),
        default='CHF',
        fieldset=_('Payments'),
        depends_on=(
            'pricing_method', '!inherit',
            'pricing_method', '!free',
        ),
        validators=[InputRequired()],
    )

    access = RadioField(
        label=_('Access'),
        choices=(
            ('public', _('Public')),
            ('private', _('Only by privileged users')),
            ('member', _('Only by privileged users and members')),
        ),
        default='public',
        fieldset=_('Security')
    )

    def on_request(self) -> None:
        if not self.request.app.org.holidays:
            self.delete_field('on_holidays')
        if not self.request.app.org.has_school_holidays:
            self.delete_field('during_school_holidays')

    def ensure_start_before_end(self) -> bool | None:
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                assert isinstance(self.start.errors, list)
                self.start.errors.append(_('Start date before end date'))
                return False
        return None

    @property
    def weekdays(self) -> list[int]:
        """ The rrule weekdays derived from the except_for field. """
        exceptions = set(self.except_for.data or ())
        return [d[0] for d in WEEKDAYS if d[0] not in exceptions]

    @cached_property
    def exceptions(self) -> DateContainer:
        if not hasattr(self, 'request'):
            return ()

        if not self.on_holidays:
            return ()

        if self.on_holidays.data == 'yes':
            return ()

        return self.request.app.org.holidays

    @cached_property
    def ranged_exceptions(self) -> Sequence[tuple[date, date]]:
        if not hasattr(self, 'request'):
            return ()

        if not self.during_school_holidays:
            return ()

        if self.during_school_holidays.data == 'yes':
            return ()

        return tuple(self.request.app.org.school_holidays)

    def is_excluded(self, dt: datetime) -> bool:
        date = dt.date()
        if date in self.exceptions:
            return True

        for start, end in self.ranged_exceptions:
            if start <= date <= end:
                return True
        return False

    @property
    def dates(self) -> SequenceOrScalar[tuple[datetime, datetime]]:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def whole_day(self) -> bool:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def partly_available(self) -> bool:
        """  Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def quota(self) -> int:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    @property
    def quota_limit(self) -> int:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        raise NotImplementedError

    # FIXME: This collides with Form.data which is not ideal, we should
    #        probably choose a different name for this
    @property
    def data(self) -> dict[str, Any]:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        return {
            'pricing_method': self.pricing_method.data,
            'price_per_item': self.price_per_item.data,
            'price_per_hour': self.price_per_hour.data,
            'currency': self.currency.data,
            'access': self.access.data
        }


class AllocationEditForm(Form, AllocationFormHelpers):
    """ Baseform for edit forms. Edit forms differ from the base allocation
    form somewhat, since they don't offer a way to generate more than
    one allocation at a time.

    The dates property is therefore expected to return a single start, end
    dates tuple.

    """

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        fieldset=_('Date')
    )

    pricing_method = RadioField(
        label=_('Price'),
        fieldset=_('Payments'),
        default='inherit',
        validators=[InputRequired()],
        choices=(
            ('inherit', _('Inherit from resource')),
            ('free', _('Free of charge')),
            ('per_item', _('Per item')),
            ('per_hour', _('Per hour'))
        )
    )

    price_per_item = DecimalField(
        label=_('Price per item'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_item')
    )

    price_per_hour = DecimalField(
        label=_('Price per hour'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_hour')
    )

    currency = StringField(
        label=_('Currency'),
        default='CHF',
        fieldset=_('Payments'),
        depends_on=(
            'pricing_method', '!inherit',
            'pricing_method', '!free',
        ),
        validators=[InputRequired()],
    )

    access = RadioField(
        label=_('Access'),
        choices=(
            ('public', _('Public')),
            ('private', _('Only by privileged users')),
            ('member', _('Only by privileged users and members')),
        ),
        default='public',
        fieldset=_('Security')
    )

    # FIXME: same here
    @property
    def data(self) -> dict[str, Any]:
        """ Passed to :meth:`libres.db.scheduler.Scheduler.allocate`. """
        return {
            'pricing_method': self.pricing_method.data,
            'price_per_item': self.price_per_item.data,
            'price_per_hour': self.price_per_hour.data,
            'currency': self.currency.data,
            'access': self.access.data
        }

    def apply_data(self, data: dict[str, Any] | None) -> None:
        if not data:
            return
        if 'access' in data:
            self.access.data = data['access']
        if 'pricing_method' in data:
            self.pricing_method.data = data['pricing_method']
        if 'price_per_item' in data:
            self.price_per_item.data = data['price_per_item']
        if 'price_per_hour' in data:
            self.price_per_hour.data = data['price_per_hour']
        if 'currency' in data:
            self.currency.data = data['currency']


class Daypasses:

    daypasses = IntegerField(
        label=_('Daypasses'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Daypasses')
    )

    daypasses_limit = IntegerField(
        label=_('Daypasses Limit'),
        validators=[
            InputRequired(),
            NumberRange(0, 999)
        ],
        fieldset=_('Daypasses')
    )


class DaypassAllocationForm(AllocationForm, Daypasses):

    whole_day = True
    partly_available = False

    @property
    def quota(self) -> int:
        return self.daypasses.data  # type:ignore[return-value]

    @property
    def quota_limit(self) -> int:
        return self.daypasses_limit.data  # type:ignore[return-value]

    @property
    def dates(self) -> Sequence[tuple[datetime, datetime]]:
        return self.generate_dates(
            self.start.data,
            self.end.data,
            weekdays=self.weekdays
        )


class DaypassAllocationEditForm(AllocationEditForm, Daypasses):

    whole_day = True
    partly_available = False

    @property
    def quota(self) -> int:
        return self.daypasses.data  # type:ignore[return-value]

    @property
    def quota_limit(self) -> int:
        return self.daypasses_limit.data  # type:ignore[return-value]

    @property
    def dates(self) -> tuple[datetime, datetime]:
        assert self.date.data is not None
        return (
            sedate.as_datetime(self.date.data),
            sedate.as_datetime(self.date.data) + timedelta(
                days=1, microseconds=-1
            )
        )

    def apply_dates(self, start: datetime, end: datetime) -> None:
        self.date.data = start.date()

    def apply_model(self, model: Allocation) -> None:
        self.apply_data(model.data)
        self.date.data = model.display_start().date()
        self.daypasses.data = model.quota
        self.daypasses_limit.data = model.quota_limit


class RoomAllocationForm(AllocationForm):

    as_whole_day = RadioField(
        label=_('Whole day'),
        choices=[
            ('yes', _('Yes')),
            ('no', _('No'))
        ],
        default='no',
        fieldset=_('Time')
    )

    start_time = TimeField(
        label=_('Each starting at'),
        description=_('HH:MM'),
        validators=[InputRequired()],
        fieldset=_('Time'),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_('Each ending at'),
        description=_('HH:MM'),
        validators=[InputRequired()],
        fieldset=_('Time'),
        depends_on=('as_whole_day', 'no')
    )

    is_partly_available = RadioField(
        label=_('May be partially reserved'),
        choices=[
            ('yes', _('Yes')),
            ('no', _('No'))
        ],
        default='yes',
        fieldset=_('Time'),
        depends_on=('as_whole_day', 'no')
    )

    per_time_slot = IntegerField(
        label=_('Reservations per time slot'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Time'),
        default=1,
        depends_on=('as_whole_day', 'no', 'is_partly_available', 'no')
    )

    quota_limit = 1

    @property
    def quota(self) -> int:
        return self.per_time_slot.data  # type:ignore[return-value]

    @property
    def whole_day(self) -> bool:
        return self.as_whole_day.data == 'yes'

    @property
    def partly_available(self) -> bool:
        if self.whole_day:
            # Hiding a field will still pass the default, we catch it here
            return False
        return self.is_partly_available.data == 'yes'

    @property
    def dates(self) -> Sequence[tuple[datetime, datetime]]:
        return self.generate_dates(
            self.start.data,
            self.end.data,
            self.start_time.data,
            self.end_time.data,
            self.weekdays
        )


class DailyItemFields:

    items = IntegerField(
        label=_('Available items'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Options'),
        default=1,
    )

    item_limit = IntegerField(
        label=_('Reservations per time slot and person'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Options'),
        default=1,
    )


class DailyItemAllocationForm(AllocationForm, DailyItemFields):

    whole_day = True
    partly_available = False

    @property
    def quota(self) -> int:
        return self.items.data  # type:ignore[return-value]

    @property
    def quota_limit(self) -> int:
        return self.item_limit.data  # type:ignore[return-value]

    @property
    def dates(self) -> Sequence[tuple[datetime, datetime]]:
        return self.generate_dates(
            self.start.data,
            self.end.data,
            weekdays=self.weekdays
        )


class DailyItemAllocationEditForm(AllocationEditForm, DailyItemFields):
    whole_day = True
    partly_available = False

    @property
    def quota(self) -> int:
        return self.items.data  # type:ignore[return-value]

    @property
    def quota_limit(self) -> int:
        return self.item_limit.data  # type:ignore[return-value]

    @property
    def dates(self) -> tuple[datetime, datetime]:
        assert self.date.data is not None
        return (
            sedate.as_datetime(self.date.data),
            sedate.as_datetime(self.date.data) + timedelta(
                days=1, microseconds=-1
            )
        )

    def apply_dates(self, start: datetime, end: datetime) -> None:
        self.date.data = start.date()

    def apply_model(self, model: Allocation) -> None:
        self.apply_data(model.data)
        self.date.data = model.display_start().date()
        self.items.data = model.quota
        self.item_limit.data = model.quota_limit


class RoomAllocationEditForm(AllocationEditForm):

    as_whole_day = RadioField(
        label=_('Whole day'),
        choices=[
            ('yes', _('Yes')),
            ('no', _('No'))
        ],
        default='yes',
        fieldset=_('Time')
    )

    start_time = TimeField(
        label=_('From'),
        description=_('HH:MM'),
        validators=[DataRequired()],
        fieldset=_('Time'),
        depends_on=('as_whole_day', 'no')
    )

    end_time = TimeField(
        label=_('Until'),
        description=_('HH:MM'),
        validators=[DataRequired()],
        fieldset=_('Time'),
        depends_on=('as_whole_day', 'no')
    )

    per_time_slot = IntegerField(
        label=_('Slots per Reservation'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Options'),
        default=1,
        depends_on=('as_whole_day', 'no')
    )

    def ensure_start_before_end(self) -> bool | None:
        if self.whole_day:
            return None

        assert self.start_time.data is not None
        assert self.end_time.data is not None
        if self.start_time.data >= self.end_time.data:
            assert isinstance(self.start_time.errors, list)
            self.start_time.errors.append(_('Start time before end time'))
            return False
        return None

    quota_limit = 1

    @property
    def quota(self) -> int:
        return self.per_time_slot.data  # type:ignore[return-value]

    @property
    def whole_day(self) -> bool:
        return self.as_whole_day.data == 'yes'

    @property
    def partly_available(self) -> bool:
        return self.model.partly_available

    @property
    def dates(self) -> tuple[datetime, datetime]:
        if self.whole_day:
            assert self.date.data is not None
            return (
                sedate.as_datetime(self.date.data),
                sedate.as_datetime(self.date.data) + timedelta(
                    days=1, microseconds=-1
                )
            )
        else:
            return (  # type:ignore[return-value]
                self.combine_datetime('date', 'start_time'),
                self.combine_datetime('date', 'end_time'),
            )

    def apply_dates(self, start: datetime, end: datetime) -> None:
        self.date.data = start.date()
        self.start_time.data = start.time()
        self.end_time.data = end.time()

    def apply_model(self, model: Allocation) -> None:
        self.apply_data(model.data)
        self.apply_dates(model.display_start(), model.display_end())
        self.as_whole_day.data = model.whole_day and 'yes' or 'no'
        self.per_time_slot.data = model.quota

    def on_request(self) -> None:
        if self.partly_available:
            self.hide(self.as_whole_day)
            self.hide(self.per_time_slot)
