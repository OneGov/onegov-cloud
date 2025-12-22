from __future__ import annotations

from sedate import to_timezone
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from onegov.form import Form
from onegov.form.fields import ChosenSelectField, TimeField
from onegov.translator_directory import _
from onegov.translator_directory.utils import (
    calculate_distance_to_location
)
from onegov.translator_directory.constants import (
    FINANZSTELLE,
    ASSIGNMENT_LOCATIONS,
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
        TranslatorTimeReport
    )
    from onegov.translator_directory.models.translator import Translator
    from onegov.translator_directory.request import TranslatorAppRequest


class TranslatorTimeReportForm(Form):
    """Form for creating/editing translator time reports."""

    request: TranslatorAppRequest

    assignment_type = ChosenSelectField(
        label=_('Type of translation/interpreting'),
        choices=[],
        validators=[InputRequired()],
        default='on-site',
    )

    assignment_location = ChosenSelectField(
        label=_('Assignment Location'),
        choices=[],  # will be set in on_request
        validators=[Optional()],
        depends_on=('assignment_type', 'on-site'),
    )

    # Used only in edit mode - hidden when creating new reports
    # If assignment_location_override is set, assignment_location
    # should be ignored. This allows for the possibility of setting
    # a location which differs from pre-determined set of possible
    # locations.
    assignment_location_override = StringField(
        label=_('Location Override (manual entry)'),
        validators=[Optional()],
        description=_(
            'Enter a custom location address. Travel compensation '
            'will be calculated based on the geocoded location. '
            'Example: Beckenstube 1, 8200 Schaffhausen'
        ),
    )

    finanzstelle = ChosenSelectField(
        label=_('Cost center'),
        choices=[],
        validators=[InputRequired()],
        default='polizei',
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

    break_time = TimeField(
        label=_('Break time'),
        validators=[Optional()],
        default=time(0, 0),
    )

    case_number = StringField(
        label=_('Case Number'),
        validators=[InputRequired()],
    )

    is_urgent = BooleanField(
        label=_('Exceptionally urgent'),
        description=_('25% surcharge'),
        default=False,
    )

    skip_travel_calculation = BooleanField(
        label=_('ohne Wegberechnung'),
        description=_('No travel compensation will be calculated'),
        default=False,
        depends_on=('assignment_type', 'on-site'),
    )

    notes = TextAreaField(
        label=_('Notes'), validators=[Optional()], render_kw={'rows': 3}
    )

    def validate_assignment_location(self, field: ChosenSelectField) -> None:
        if self.assignment_type.data != 'on-site':
            return
        else:
            if not field.data:
                raise ValidationError(_('Please select a location'))

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
        self.assignment_location.choices = [
            (key, name) for key, (name, _) in ASSIGNMENT_LOCATIONS.items()
        ]
        self.finanzstelle.choices = [
            (key, fs.name) for key, fs in FINANZSTELLE.items()
        ]

    def get_hourly_rate(self, translator: Translator) -> Decimal:
        """Determine hourly rate based on translator certification."""
        if translator.admission == 'certified':
            return HOURLY_RATE_CERTIFIED
        return HOURLY_RATE_UNCERTIFIED

    def get_datetime_range(self) -> tuple[datetime, datetime]:
        """Get start and end datetime with proper types."""
        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert self.end_time.data is not None

        start_dt = datetime.combine(self.start_date.data, self.start_time.data)
        end_dt = datetime.combine(self.end_date.data, self.end_time.data)
        return start_dt, end_dt

    def get_duration_hours(self) -> Decimal:
        """Calculate duration in hours from start/end times, rounded.

        Calculates raw time between start and end (ignoring breaks for now).
        """
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

        # Ensure hours is not negative
        if hours < 0:
            hours = Decimal('0')

        # Round to nearest 0.5 hour
        hours_times_two = hours * Decimal('2')
        rounded = hours_times_two.to_integral_value(rounding='ROUND_CEILING')
        return rounded / Decimal('2')

    def calculate_night_hours(self) -> Decimal:
        """Calculate actual hours worked during night (20:00-06:00)."""
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

        # Calculate night hours by iterating through time range
        night_seconds = 0
        current = start_dt

        while current < end_dt:
            # Determine if current time is in night period (20:00-06:00)
            current_time = current.time()
            is_night = current_time >= time(20, 0) or current_time < time(6, 0)

            if is_night:
                # Find the end of current night period
                if current_time >= time(20, 0):
                    # Night goes until 06:00 next day
                    period_end = datetime.combine(
                        current.date() + timedelta(days=1), time(6, 0)
                    )
                else:
                    # We're in early morning (before 06:00)
                    period_end = datetime.combine(current.date(), time(6, 0))

                # Calculate overlap
                segment_end = min(end_dt, period_end)
                night_seconds += int((segment_end - current).total_seconds())
                current = segment_end
            else:
                # We're in day period (06:00-20:00), skip to next night
                next_night = datetime.combine(current.date(), time(20, 0))
                if next_night <= current:
                    next_night = datetime.combine(
                        current.date() + timedelta(days=1), time(20, 0)
                    )
                current = min(end_dt, next_night)

        # Convert to hours
        night_hours = Decimal(night_seconds) / Decimal(3600)

        # Round to nearest 0.5 hour (same as total duration rounding)
        night_hours_times_two = night_hours * Decimal('2')
        rounded = night_hours_times_two.to_integral_value(
            rounding='ROUND_CEILING'
        )
        return rounded / Decimal('2')

    def calculate_weekend_holiday_hours(self) -> Decimal:
        """Calculate actual hours worked during weekends or public holidays.

        Counts hours that fall on:
        - Saturday or Sunday (any time)
        - Public holidays (any time)

        Returns hours as Decimal, rounded to nearest 0.5 hour.
        """
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

        # Get holidays if available
        holidays: set[date] = set()
        if self.request and self.request.app.org.holidays:
            holiday_list = self.request.app.org.holidays.between(
                self.start_date.data, self.end_date.data
            )
            holidays = {dt for dt, _ in holiday_list}

        # Calculate weekend/holiday hours by iterating through time range
        weekend_holiday_seconds = 0
        current = start_dt

        # Process day by day
        while current < end_dt:
            current_date = current.date()
            is_weekend = current_date.weekday() >= 5  # Sat or Sun
            is_holiday = current_date in holidays

            if is_weekend or is_holiday:
                # Find end of current day
                day_end = datetime.combine(
                    current_date + timedelta(days=1), time(0, 0)
                )
                segment_end = min(end_dt, day_end)
                weekend_holiday_seconds += int(
                    (segment_end - current).total_seconds()
                )
                current = segment_end
            else:
                # Skip to next day
                next_day = datetime.combine(
                    current_date + timedelta(days=1), time(0, 0)
                )
                current = min(end_dt, next_day)

        # Convert to hours
        weekend_holiday_hours = Decimal(weekend_holiday_seconds) / Decimal(
            3600
        )

        # Round to nearest 0.5 hour
        weekend_holiday_hours_times_two = weekend_holiday_hours * Decimal('2')
        rounded = weekend_holiday_hours_times_two.to_integral_value(
            rounding='ROUND_CEILING'
        )
        return rounded / Decimal('2')

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

        # Load existing time report data
        if formdata is None and obj is not None:
            if hasattr(obj, 'start') and obj.start:
                # Convert UTC to Europe/Zurich timezone before
                # extracting date/time
                local_start = to_timezone(obj.start, 'Europe/Zurich')
                self.start_date.data = local_start.date()
                self.start_time.data = local_start.time()
            elif hasattr(obj, 'assignment_date'):
                self.start_date.data = obj.assignment_date

            if hasattr(obj, 'end') and obj.end:
                # Convert UTC to Europe/Zurich timezone before
                # extracting date/time
                local_end = to_timezone(obj.end, 'Europe/Zurich')
                self.end_date.data = local_end.date()
                self.end_time.data = local_end.time()
            elif hasattr(obj, 'assignment_date'):
                self.end_date.data = obj.assignment_date

            if hasattr(obj, 'break_time'):
                break_minutes = getattr(obj, 'break_time', 0)
                if break_minutes:
                    hours = break_minutes // 60
                    minutes = break_minutes % 60
                    self.break_time.data = time(hours, minutes)

            if hasattr(obj, 'surcharge_types'):
                surcharge_types = getattr(obj, 'surcharge_types', None)
                if surcharge_types:
                    self.is_urgent.data = 'urgent' in surcharge_types

            if hasattr(obj, 'finanzstelle'):
                self.finanzstelle.data = getattr(obj, 'finanzstelle', None)

            if hasattr(obj, 'assignment_type'):
                self.assignment_type.data = getattr(
                    obj, 'assignment_type', None
                )

            if hasattr(obj, 'assignment_location'):
                location = getattr(obj, 'assignment_location', None)
                if location:
                    if location in ASSIGNMENT_LOCATIONS:
                        self.assignment_location.data = location
                    else:
                        self.assignment_location_override.data = location

    def get_surcharge_types(self) -> list[str]:
        """Get list of active surcharge types from form based on actual
        hours."""
        types: list[str] = []
        if self.calculate_night_hours() > 0:
            types.append('night_work')
        if self.calculate_weekend_holiday_hours() > 0:
            types.append('weekend_holiday')
        if self.is_urgent.data:
            types.append('urgent')
        return types

    def calculate_travel_details(
        self,
        translator: Translator,
        request: TranslatorAppRequest | None = None
    ) -> tuple[Decimal, float | None]:
        """Calculate travel compensation and distance.

        For on-site assignments with a selected location, calculates distance
        from translator's address to the assignment location.
        The distance is multiplied by 2 to account for round trip.
        """
        if (
            self.skip_travel_calculation.data
            and self.assignment_type.data == 'on-site'
        ):
            return Decimal('0'), 0.0

        if self.assignment_type.data in ('telephonic', 'schriftlich'):
            return Decimal('0'), None

        distance = None
        one_way_km = None

        # Try to calculate distance (handles both dropdown and override)
        if (
            self.assignment_type.data == 'on-site'
            and request
            and translator.coordinates
        ):
            location_key = self.assignment_location.data or ''
            custom_address = None
            custom_address = self.assignment_location_override.data or None

            one_way_distance = calculate_distance_to_location(
                request, translator.coordinates, location_key, custom_address
            )
            if one_way_distance is not None:
                one_way_km = one_way_distance
                distance = one_way_distance * 2

        # Fall back to translator's pre-calculated drive_distance
        if distance is None and translator.drive_distance:
            one_way_km = float(translator.drive_distance)
            distance = float(translator.drive_distance) * 2

        # No distance available
        if distance is None:
            return Decimal('0'), None

        # Apply compensation tiers
        compensation = Decimal('0')
        if distance <= 25:
            compensation = Decimal('20')
        elif distance <= 50:
            compensation = Decimal('50')
        elif distance <= 100:
            compensation = Decimal('100')
        else:
            compensation = Decimal('150')

        return compensation, one_way_km

    def get_travel_compensation(
        self,
        translator: Translator,
        request: TranslatorAppRequest | None = None
    ) -> Decimal:

        compensation, _ = self.calculate_travel_details(translator, request)
        return compensation

    def update_model(self, model: TranslatorTimeReport) -> None:
        """Update the time report model with form data."""
        from sedate import replace_timezone

        assert self.start_date.data is not None
        assert self.start_time.data is not None
        assert self.end_date.data is not None
        assert self.end_time.data is not None

        assert self.assignment_type.data is not None
        model.assignment_type = self.assignment_type.data
        model.assignment_location = self.assignment_location.data or None
        model.finanzstelle = self.finanzstelle.data

        # Handle location override (only in edit mode)
        if self.assignment_location_override.data:
            model.assignment_location = self.assignment_location_override.data
        else:
            model.assignment_location = self.assignment_location.data or None

        duration_hours = self.get_duration_hours()
        model.duration = int(float(duration_hours) * 60)

        # Store break time in minutes
        if self.break_time.data:
            break_minutes = (
                self.break_time.data.hour * 60 + self.break_time.data.minute
            )
            model.break_time = break_minutes
        else:
            model.break_time = 0

        # Calculate and store night hours (in minutes)
        night_hours = self.calculate_night_hours()
        model.night_minutes = int(float(night_hours) * 60)

        # Calculate and store weekend/holiday hours (in minutes)
        weekend_holiday_hours = self.calculate_weekend_holiday_hours()
        model.weekend_holiday_minutes = int(float(weekend_holiday_hours) * 60)

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

        travel_comp, travel_distance = self.calculate_travel_details(
            model.translator, self.request
        )
        model.travel_compensation = travel_comp
        model.travel_distance = travel_distance

        # Use centralized calculation from model
        breakdown = model.calculate_compensation_breakdown()
        model.total_compensation = breakdown['total']
