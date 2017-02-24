import isodate
import json

from cached_property import cached_property
from collections import namedtuple
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period, PeriodCollection
from onegov.feriennet import _
from onegov.form import Form
from sedate import to_timezone, standardize_date, overlaps
from sqlalchemy import desc
from wtforms.fields import BooleanField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import DecimalField, IntegerField
from wtforms.validators import InputRequired, NumberRange, Optional


class OccasionForm(Form):

    timezone = 'Europe/Zurich'

    period_id = SelectField(
        label=_("Period"),
        validators=[InputRequired()],
        default='0xdeadbeef')

    dates = StringField(
        label=_("Dates"),
        render_kw={'class_': 'many many-datetime-ranges'}
    )

    meeting_point = StringField(
        label=_("Meeting Point")
    )

    note = TextAreaField(
        label=_("Note"),
        render_kw={'rows': 4}
    )

    cost = DecimalField(
        label=_("Cost"),
        description=_("The amount paid to the organiser"),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ]
    )

    min_spots = IntegerField(
        label=_("Minimum Number of Participants"),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ],
        fieldset=_("Participants")
    )

    max_spots = IntegerField(
        label=_("Maximum Number of Participants"),
        validators=[
            InputRequired(),
            NumberRange(1, 10000)
        ],
        fieldset=_("Participants")
    )

    min_age = IntegerField(
        label=_("Minimum Age"),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_("Participants")
    )

    max_age = IntegerField(
        label=_("Maximum Age"),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_("Participants")
    )

    exclude_from_overlap_check = BooleanField(
        label=_("Bookings to this occasion may overlap with other bookings"),
        fieldset=_("Advanced"),
        default=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_errors = {}

    @cached_property
    def selected_period(self):
        return PeriodCollection(self.request.app.session()).by_id(
            self.period_id.data)

    @cached_property
    def parsed_dates(self):
        result = []

        DateRange = namedtuple('DateRange', ['start', 'end'])

        for date in json.loads(self.dates.data or '{}').get('values', []):
            try:
                start = isodate.parse_datetime(date['start'].replace(' ', 'T'))
                end = isodate.parse_datetime(date['end'].replace(' ', 'T'))
            except isodate.isoerror.ISO8601Error:
                continue

            result.append(DateRange(
                start=standardize_date(start, self.timezone),
                end=standardize_date(end, self.timezone)
            ))

        return result

    def setup_period_choices(self):
        query = PeriodCollection(self.request.app.session()).query()
        query = query.order_by(desc(Period.active), Period.title)

        def choice(period):
            return str(period.id), '{} ({:%d.%m.%Y} - {:%d.%m.%Y})'.format(
                period.title,
                period.execution_start,
                period.execution_end
            )

        periods = query.all()
        self.period_id.choices = [choice(p) for p in periods]

        if self.period_id.data == '0xdeadbeef':
            self.period_id.data = periods[0].id

    def on_request(self):
        self.setup_period_choices()
        self.dates.data = self.dates_to_json(self.parsed_dates)

    def ensure_at_least_one_date(self):
        if not self.parsed_dates:
            self.dates.errors = [_("Must specify at least one date")]
            return False

    def ensure_valid_dates(self):
        valid = True

        min_start = self.selected_period.execution_start
        min_end = self.selected_period.execution_end

        for index, d in enumerate(self.parsed_dates):
            start_date = to_timezone(d.start, self.timezone).date()
            end_date = to_timezone(d.end, self.timezone).date()

            if d.start > d.end:
                self.date_errors[index] = self.request.translate(_(
                    "The end date must be after the start date"
                ))
                valid = False

            if start_date < min_start or min_end < start_date:
                self.date_errors[index] = self.request.translate(_(
                    "The date is outside the selected period"
                ))
                valid = False

            if end_date < min_start or min_end < end_date:
                self.date_errors[index] = self.request.translate(_(
                    "The date is outside the selected period"
                ))
                valid = False

            for subindex, subd in enumerate(self.parsed_dates):
                if index != subindex:
                    if overlaps(d.start, d.end, subd.start, subd.end):
                        self.date_errors[index] = self.request.translate(_(
                            "The date overlaps with another in this occasion"
                        ))
                        valid = False

        if not valid and not self.dates.errors:
            self.dates.errors = [_("Date validation failed")]

        return valid

    def ensure_max_age_after_min_age(self):
        if self.min_age.data and self.max_age.data:
            if self.min_age.data > self.max_age.data:
                self.min_age.errors.append(_(
                    "The minium age cannot be higher than the maximum age"
                ))
                return False

    def ensure_max_spots_after_min_spots(self):
        if self.min_spots.data and self.max_spots.data:
            if self.min_spots.data > self.max_spots.data:
                self.min_spots.errors.append(_(
                    "The minium number of participants cannot be higher "
                    "than the maximum number of participants"
                ))
                return False

    def ensure_max_spots_higher_than_accepted_bookings(self):
        if isinstance(self.model, Occasion):
            if len(self.model.accepted) > self.max_spots.data:
                self.max_spots.errors.append(_(
                    "The maximum number of spots is lower than the number "
                    "of already accepted bookings."
                ))
                return False

    def dates_to_json(self, dates=None):
        dates = dates or []

        def as_json_date(date):
            return to_timezone(date, self.timezone)\
                .replace(tzinfo=None).isoformat()

        if self.parsed_dates:
            self.ensure_valid_dates()  # XXX fills the error values

        return json.dumps({
            'labels': {
                'start': self.request.translate(_("Start")),
                'end': self.request.translate(_("End")),
                'add': self.request.translate(_("Add")),
                'remove': self.request.translate(_("Remove")),
            },
            'values': [
                {
                    'start': as_json_date(d.start),
                    'end': as_json_date(d.end),
                    'error': self.date_errors.get(ix, "")
                } for ix, d in enumerate(dates)
            ]
        })

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'dates',
            'max_spots',
            'min_spots',
            'min_age',
            'max_age'
        })

        assert self.parsed_dates, "should have been caught earlier"

        occasions = OccasionCollection(self.request.app.session())
        occasions.clear_dates(model)

        for date in sorted(self.parsed_dates):
            occasions.add_date(model, date.start, date.end, self.timezone)

        model.age = OccasionCollection.to_half_open_interval(
            self.min_age.data, self.max_age.data)

        model.spots = OccasionCollection.to_half_open_interval(
            self.min_spots.data, self.max_spots.data)

    def process_obj(self, model):
        super().process_obj(model)

        self.dates.data = self.dates_to_json(model.dates)

        self.min_age.data = model.age.lower
        self.max_age.data = model.age.upper - 1

        self.min_spots.data = model.spots.lower
        self.max_spots.data = model.spots.upper - 1
