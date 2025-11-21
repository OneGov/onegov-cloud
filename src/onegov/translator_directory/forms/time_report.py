from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from onegov.form import Form
from onegov.form.fields import ChosenSelectField, TimeField
from onegov.translator_directory import _
from onegov.translator_directory.constants import (
    HOURLY_RATE_CERTIFIED,
    HOURLY_RATE_UNCERTIFIED,
    TIME_REPORT_INTERPRETING_TYPES
)
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.models.time_report import (
        TranslatorTimeReport,
    )
    from onegov.translator_directory.models.translator import Translator
    from onegov.translator_directory.request import TranslatorAppRequest


class TranslatorTimeReportForm(Form):
    """Form for creating/editing translator time reports."""

    request: TranslatorAppRequest

    assignment_type = ChosenSelectField(
        label=_('Type of translation/interpreting'),
        choices=[],
        default='on-site',
    )

    start_date = DateField(
        label=_('Start date'),
        validators=[InputRequired()],
        default=date.today,
    )

    start_time = TimeField(
        label=_('Start time'),
        validators=[InputRequired()],
    )

    end_date = DateField(
        label=_('End date'),
        validators=[InputRequired()],
        default=date.today,
    )

    end_time = TimeField(
        label=_('End time'),
        validators=[InputRequired()],
    )

    case_number = StringField(
        label=_('Case number (Police)'),
        validators=[Optional()],
        description=_('Geschäftsnummer Police for linking if needed'),
    )

    is_urgent = BooleanField(
        label=_('Exceptionally urgent'),
        description=_('25% surcharge'),
        default=False,
    )

    notes = TextAreaField(
        label=_('Notes'), validators=[Optional()], render_kw={'rows': 3}
    )

    def validate_end_time(self, field: TimeField) -> None:
        if not all(
            [
                self.start_date.data,
                self.start_time.data,
                self.end_date.data,
                field.data,
            ]
        ):
            return

        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert field.data is not None

        start_dt = datetime.combine(self.start_date.data, self.start_time.data)
        end_dt = datetime.combine(self.end_date.data, field.data)

        if end_dt <= start_dt:
            raise ValidationError(_('End time must be after start time'))

    def on_request(self) -> None:
        self.assignment_type.choices = [
            (key, self.request.translate(value))
            for key, value in TIME_REPORT_INTERPRETING_TYPES.items()
        ]

    def get_hourly_rate(self, translator: Translator) -> Decimal:
        """Determine hourly rate based on translator certification."""
        if translator.admission == 'certified':
            return HOURLY_RATE_CERTIFIED
        return HOURLY_RATE_UNCERTIFIED

    def get_duration_hours(self) -> Decimal:
        """Calculate duration in hours from start/end times, rounded."""
        if not all(
            [
                self.start_date.data,
                self.start_time.data,
                self.end_date.data,
                self.end_time.data,
            ]
        ):
            return Decimal('0')

        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert self.end_time.data is not None

        start_dt = datetime.combine(self.start_date.data, self.start_time.data)
        end_dt = datetime.combine(self.end_date.data, self.end_time.data)
        duration = end_dt - start_dt
        hours = Decimal(duration.total_seconds()) / Decimal(3600)
        hours_times_two = hours * Decimal('2')
        rounded = hours_times_two.to_integral_value(rounding='ROUND_CEILING')
        return rounded / Decimal('2')

    def is_night_work(self) -> bool:
        """Check if work period overlaps with night hours (20:00-06:00)."""
        if not all(
            [
                self.start_date.data,
                self.start_time.data,
                self.end_date.data,
                self.end_time.data,
            ]
        ):
            return False

        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert self.end_time.data is not None

        night_start = time(20, 0)
        night_end = time(6, 0)
        start_t = self.start_time.data
        end_t = self.end_time.data

        if start_t >= night_start or start_t < night_end:
            return True
        if end_t >= night_start or end_t <= night_end:
            return True
        if self.start_date.data != self.end_date.data:
            return True

        return False

    def is_weekend_or_holiday(self) -> bool:
        """Check if assignment is on weekend (Sat/Sun)."""
        if not self.start_date.data:
            return False
        return self.start_date.data.weekday() >= 5

    def calculate_surcharge(self) -> Decimal:
        """Calculate total surcharge percentage."""
        surcharge = Decimal('0')
        if self.is_night_work():
            surcharge += Decimal('50')
        if self.is_weekend_or_holiday():
            surcharge += Decimal('25')
        if self.is_urgent.data:
            surcharge += Decimal('25')
        return surcharge

    def populate_obj(  # type: ignore[override]
        self, obj: TranslatorTimeReport  # type: ignore[override]
    ) -> None:
        """Populate the model from form, converting hours to minutes."""
        duration_hours = self.get_duration_hours()
        obj.duration = int(float(duration_hours) * 60)

    def process(  # type: ignore[override]
        self, formdata: object = None, obj: object = None, **kwargs: object
    ) -> None:
        """Process form data for editing existing time reports."""
        super().process(formdata, obj, **kwargs)  # type: ignore[arg-type]
        if formdata is None and obj is not None:
            if hasattr(obj, 'start') and obj.start:
                self.start_date.data = obj.start.date()
                self.start_time.data = obj.start.time()
            elif hasattr(obj, 'assignment_date'):
                self.start_date.data = obj.assignment_date

            if hasattr(obj, 'end') and obj.end:
                self.end_date.data = obj.end.date()
                self.end_time.data = obj.end.time()
            elif hasattr(obj, 'assignment_date'):
                self.end_date.data = obj.assignment_date

            if hasattr(obj, 'surcharge_types'):
                surcharge_types = getattr(obj, 'surcharge_types', None)
                if surcharge_types:
                    self.is_urgent.data = 'urgent' in surcharge_types

    def get_surcharge_types(self) -> list[str]:
        """Get list of active surcharge types from form."""
        types: list[str] = []
        if self.is_night_work():
            types.append('night_work')
        if self.is_weekend_or_holiday():
            types.append('weekend_holiday')
        if self.is_urgent.data:
            types.append('urgent')
        return types

    def get_travel_compensation(self, translator: Translator) -> Decimal:
        """Calculate travel compensation based on round trip distance.

        The drive_distance is multiplied by 2 to account for the round trip
        (Wegentschädigung * 2).
        Returns 0 for telephonic assignments.
        """
        if self.assignment_type.data == 'telephonic':
            return Decimal('0')

        if not translator.drive_distance:
            return Decimal('0')

        distance = float(translator.drive_distance) * 2
        if distance <= 25:
            return Decimal('20')
        elif distance <= 50:
            return Decimal('50')
        elif distance <= 100:
            return Decimal('100')
        else:
            return Decimal('150')

    def update_model(self, model: TranslatorTimeReport) -> None:
        """Update the time report model with form data."""
        from sedate import replace_timezone

        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert self.end_time.data is not None

        model.assignment_type = self.assignment_type.data or None

        duration_hours = self.get_duration_hours()
        model.duration = int(float(duration_hours) * 60)

        model.case_number = self.case_number.data or None
        model.assignment_date = self.start_date.data

        start_dt = datetime.combine(self.start_date.data, self.start_time.data)
        end_dt = datetime.combine(self.end_date.data, self.end_time.data)
        model.start = replace_timezone(start_dt, 'Europe/Zurich')
        model.end = replace_timezone(end_dt, 'Europe/Zurich')
        model.notes = self.notes.data or None

        hourly_rate = self.get_hourly_rate(model.translator)
        model.hourly_rate = hourly_rate

        surcharge_types = self.get_surcharge_types()
        model.surcharge_types = surcharge_types if surcharge_types else None

        surcharge_pct = self.calculate_surcharge()
        model.surcharge_percentage = surcharge_pct

        travel_comp = self.get_travel_compensation(model.translator)
        model.travel_compensation = travel_comp

        base = hourly_rate * duration_hours
        surcharge_amount = base * (surcharge_pct / Decimal(100))
        meal_allowance = (
            Decimal('40.0') if duration_hours >= 6 else Decimal('0')
        )
        model.total_compensation = (
            base + surcharge_amount + travel_comp + meal_allowance
        )
