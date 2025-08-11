from __future__ import annotations

import isodate

from decimal import Decimal
from functools import cached_property
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import BookingPeriod, BookingPeriodCollection
from onegov.core.custom import json
from onegov.feriennet import _
from onegov.form import Form
from sedate import to_timezone, standardize_date, overlaps
from sqlalchemy import desc
from wtforms.fields import BooleanField
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, NumberRange, Optional


from typing import NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from onegov.activity.models import OccasionDate
    from onegov.feriennet.request import FeriennetRequest


class OccasionForm(Form):

    request: FeriennetRequest

    timezone = 'Europe/Zurich'

    period_id = SelectField(
        label=_('Period'),
        validators=[InputRequired()],
        default='0xdeadbeef')

    dates = StringField(
        label=_('Dates'),
        render_kw={'class_': 'many many-datetime-ranges'}
    )

    meeting_point = StringField(
        label=_('Meeting Point'),
        validators=[InputRequired()]
    )

    note = TextAreaField(
        label=_('Note'),
        render_kw={'rows': 4}
    )

    cost = DecimalField(
        label=_('Cost'),
        description=_('The amount paid to the organiser'),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ]
    )

    min_spots = IntegerField(
        label=_('Minimum Number of Participants'),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ],
        fieldset=_('Participants')
    )

    max_spots = IntegerField(
        label=_('Maximum Number of Participants'),
        validators=[
            InputRequired(),
            NumberRange(1, 10000)
        ],
        fieldset=_('Participants')
    )

    min_age = IntegerField(
        label=_('Minimum Age'),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_('Participants')
    )

    max_age = IntegerField(
        label=_('Maximum Age'),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_('Participants')
    )

    exclude_from_overlap_check = BooleanField(
        label=_('Allow overlap'),
        description=_(
            'Allows bookings to this occasion to overlap with other bookings.'
        ),
        fieldset=_('Advanced'),
        default=False
    )

    exempt_from_booking_limit = BooleanField(
        label=_('Exempt from booking limit'),
        description=_(
            'Allows bookings to this occasion to be excempt from booking '
            'limits. Does not apply to matching.'
        ),
        fieldset=_('Advanced'),
        default=False
    )

    administrative_cost = RadioField(
        label=_('The administrative cost of each booking'),
        choices=(
            ('default', _('Use default costs defined by the period')),
            ('custom', _('Use custom costs')),
        ),
        fieldset=_('Advanced'),
        default='default'
    )

    administrative_cost_amount = DecimalField(
        label=_('Administrative cost'),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        fieldset=_('Advanced'),
        depends_on=('administrative_cost', 'custom')
    )

    if TYPE_CHECKING:
        date_errors: dict[int, str]
    else:
        # NOTE: We want to retain the original signature
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.date_errors = {}

    @property
    def booking_cost(self) -> Decimal | None:
        if not self.administrative_cost:
            return None

        if self.administrative_cost.data == 'default':
            return None

        return self.administrative_cost_amount.data or Decimal(0)

    @booking_cost.setter
    def booking_cost(self, amount: Decimal | None) -> None:
        if not self.administrative_cost:
            return

        if amount is None:
            self.administrative_cost.data = 'default'
            self.administrative_cost_amount.data = None
        else:
            self.administrative_cost.data = 'custom'
            self.administrative_cost_amount.data = amount

    @cached_property
    def selected_period(self) -> BookingPeriod | None:
        return BookingPeriodCollection(self.request.session).by_id(
            self.period_id.data)

    class DateRange(NamedTuple):
        start: datetime
        end: datetime

    @cached_property
    def parsed_dates(self) -> list[DateRange]:
        result = []

        for date in json.loads(self.dates.data or '{}').get('values', []):
            try:
                start = isodate.parse_datetime(date['start'].replace(' ', 'T'))
                end = isodate.parse_datetime(date['end'].replace(' ', 'T'))
            except isodate.isoerror.ISO8601Error:
                continue

            result.append(self.DateRange(
                start=standardize_date(start, self.timezone),
                end=standardize_date(end, self.timezone)
            ))

        return result

    def setup_period_choices(self) -> None:
        query = BookingPeriodCollection(self.request.session).query()
        query = query.order_by(desc(BookingPeriod.active), BookingPeriod.title)

        def choice(period: BookingPeriod) -> tuple[str, str]:
            return str(period.id), '{} ({:%d.%m.%Y} - {:%d.%m.%Y})'.format(
                period.title,
                period.execution_start,
                period.execution_end
            )

        periods = query.all()
        self.period_id.choices = [choice(p) for p in periods]

        if self.period_id.data == '0xdeadbeef':
            self.period_id.data = periods[0].id

    def on_request(self) -> None:
        self.setup_period_choices()
        self.dates.data = self.dates_to_json(self.parsed_dates)

        period = self.request.app.active_period or None

        if not period or period.all_inclusive:
            self.delete_field('administrative_cost')
            self.delete_field('administrative_cost_amount')

    def ensure_at_least_one_date(self) -> bool | None:
        if not self.parsed_dates:
            self.dates.errors = [_('Must specify at least one date')]
            return False
        return None

    def ensure_safe_period_change(self) -> bool | None:
        # the period may only be changed if there are no booking associated
        # with the occasion, otherwise this is unsafe and results in
        # bookings being moved from one period to another without the
        # ability to undo that!
        if not hasattr(self.model, 'period_id'):
            return None

        if self.request.view_name == 'clone':
            return None

        if str(self.model.period_id) != self.period_id.data:
            if self.model.bookings:
                self.period_id.errors = [
                    _(
                        'Cannot adjust period, there are bookings '
                        'linked to this occassion'
                    )
                ]
                return False
        return None

    def ensure_valid_dates(self) -> bool:
        valid = True

        assert self.selected_period is not None
        min_start = self.selected_period.execution_start
        min_end = self.selected_period.execution_end

        for index, d in enumerate(self.parsed_dates):
            start_date = to_timezone(d.start, self.timezone).date()
            end_date = to_timezone(d.end, self.timezone).date()

            if d.start > d.end:
                self.date_errors[index] = self.request.translate(_(
                    'The end date must be after the start date'
                ))
                valid = False

            if start_date < min_start or min_end < start_date:
                self.date_errors[index] = self.request.translate(_(
                    'The date is outside the selected period'
                ))
                valid = False

            if end_date < min_start or min_end < end_date:
                self.date_errors[index] = self.request.translate(_(
                    'The date is outside the selected period'
                ))
                valid = False

            for subindex, subd in enumerate(self.parsed_dates):
                if index != subindex:
                    if overlaps(d.start, d.end, subd.start, subd.end):
                        self.date_errors[index] = self.request.translate(_(
                            'The date overlaps with another in this occasion.'
                        ))
                        valid = False

        if not valid and not self.dates.errors:
            self.dates.errors = [_('Date validation failed')]

        return valid

    def ensure_min_max_age(self) -> bool | None:
        if self.min_age.data is not None and self.max_age.data is not None:
            if self.min_age.data > self.max_age.data:
                self.min_age.errors = [
                    _('Minimum age must be lower than maximum age.')]
                return False
        return None

    def ensure_max_spots_after_min_spots(self) -> bool | None:
        if self.min_spots.data and self.max_spots.data:
            if self.min_spots.data > self.max_spots.data:
                assert isinstance(self.min_spots.errors, list)
                self.min_spots.errors.append(_(
                    'The minium number of participants cannot be higher '
                    'than the maximum number of participants'
                ))
                return False
        return None

    def ensure_max_spots_higher_than_accepted_bookings(self) -> bool | None:
        if not isinstance(self.model, Occasion):
            return None

        if self.request.view_name == 'clone':
            return None

        if not self.max_spots.data:
            return None

        if len(self.model.accepted) > self.max_spots.data:
            assert isinstance(self.max_spots.errors, list)
            self.max_spots.errors.append(_(
                'The maximum number of spots is lower than the number '
                'of already accepted bookings.'
            ))
            return False
        return None

    def dates_to_json(
        self,
        dates: Sequence[DateRange | OccasionDate] | None = None
    ) -> str:

        dates = dates or []

        def as_json_date(date: datetime) -> str:
            return (
                to_timezone(date, self.timezone)
                .replace(tzinfo=None).isoformat()
            )

        if self.parsed_dates:
            self.ensure_valid_dates()  # XXX fills the error values

        return json.dumps({
            'labels': {
                'start': self.request.translate(_('Start')),
                'end': self.request.translate(_('End')),
                'add': self.request.translate(_('Add')),
                'remove': self.request.translate(_('Remove')),
            },
            'values': [
                {
                    'start': as_json_date(d.start),
                    'end': as_json_date(d.end),
                    'error': self.date_errors.get(ix, '')
                } for ix, d in enumerate(dates)
            ],
            'extra': {
                'defaultDate': (
                    self.request.app.active_period
                    and self.request.app.active_period
                        .execution_start.isoformat()
                ) or (
                    self.request.app.periods
                    and self.request.app.periods[0].execution_start.isoformat()
                ),
                'defaultTime': '08:00'
            }
        })

    def populate_obj(self, model: Occasion) -> None:  # type:ignore[override]
        super().populate_obj(model, exclude={
            'dates',
            'max_spots',
            'min_spots',
            'min_age',
            'max_age'
        })

        assert self.parsed_dates, 'should have been caught earlier'

        occasions = OccasionCollection(self.request.session)
        occasions.clear_dates(model)

        for date in sorted(self.parsed_dates):
            occasions.add_date(model, date.start, date.end, self.timezone)

        model.booking_cost = self.booking_cost

        assert self.min_age.data is not None
        assert self.max_age.data is not None
        model.age = OccasionCollection.to_half_open_interval(
            self.min_age.data, self.max_age.data)

        assert self.min_spots.data is not None
        assert self.max_spots.data is not None
        model.spots = OccasionCollection.to_half_open_interval(
            self.min_spots.data, self.max_spots.data)

    def process_obj(self, model: Occasion) -> None:  # type:ignore[override]
        super().process_obj(model)

        self.dates.data = self.dates_to_json(model.dates)

        self.min_age.data = model.age.lower
        self.max_age.data = model.age.upper - 1

        self.min_spots.data = model.spots.lower
        self.max_spots.data = model.spots.upper - 1

        self.booking_cost = model.booking_cost
