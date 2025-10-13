from __future__ import annotations

import math

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.translator_directory import _
from onegov.translator_directory.constants import INTERPRETING_TYPES
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.translator_directory.models.time_report import (
        TranslatorTimeReport,
    )
    from onegov.translator_directory.models.translator import Translator
    from onegov.translator_directory.request import TranslatorAppRequest
    from wtforms.fields.choices import _Choice


class TranslatorTimeReportForm(Form):
    """Form for creating/editing translator time reports."""

    request: TranslatorAppRequest

    assignment_type = ChosenSelectField(
        label=_('Type of translation/interpreting'),
        choices=[],
        validators=[Optional()],
    )

    duration = DecimalField(
        label=_('Duration (hours)'),
        validators=[
            InputRequired(),
            NumberRange(min=0.5, message=_('Minimum 0.5 hours')),
        ],
        render_kw={'step': '0.5', 'min': '0.5'},
    )

    case_number = StringField(
        label=_('Case number (Police)'),
        validators=[Optional()],
        description=_('Geschäftsnummer Police for linking if needed'),
    )

    assignment_date = DateField(
        label=_('Assignment date'), validators=[InputRequired()]
    )

    is_night_work = BooleanField(
        label=_('Night work (20:00 - 06:00)'),
        description=_('50% surcharge'),
        default=False,
    )

    is_weekend_holiday = BooleanField(
        label=_('Weekend or holiday'),
        description=_('25% surcharge'),
        default=False,
    )

    is_urgent = BooleanField(
        label=_('Exceptionally urgent'),
        description=_('25% surcharge'),
        default=False,
    )

    travel_distance = SelectField(
        label=_('Travel distance'), choices=[], validators=[Optional()]
    )

    notes = TextAreaField(
        label=_('Notes'), validators=[Optional()], render_kw={'rows': 3}
    )

    def on_request(self) -> None:
        self.assignment_type.choices = self.get_assignment_type_choices()
        self.travel_distance.choices = self.get_travel_choices()

    def get_assignment_type_choices(self) -> list[_Choice]:
        """Return assignment type choices."""
        return [
            (key, self.request.translate(value))
            for key, value in INTERPRETING_TYPES.items()
        ]

    def get_travel_choices(self) -> list[_Choice]:
        """Return travel distance choices with compensation."""
        return [
            ('0', self.request.translate(_('No travel'))),
            ('20', self.request.translate(_('Up to 25 km (CHF 20)'))),
            ('50', self.request.translate(_('25-50 km (CHF 50)'))),
            ('100', self.request.translate(_('50-100 km (CHF 100)'))),
            ('150', self.request.translate(_('Over 100 km (CHF 150)'))),
        ]

    def get_hourly_rate(self, translator: Translator) -> float:
        """Determine hourly rate based on translator certification."""
        if translator.admission == 'certified':
            return 90.0
        return 75.0

    def calculate_surcharge(self) -> float:
        """Calculate total surcharge percentage."""
        surcharge = 0.0
        if self.is_night_work.data:
            surcharge += 50.0
        if self.is_weekend_holiday.data:
            surcharge += 25.0
        if self.is_urgent.data:
            surcharge += 25.0
        return surcharge

    def populate_obj(  # type: ignore[override]
        self, obj: TranslatorTimeReport  # type: ignore[override]
    ) -> None:
        """Populate the model from form, converting hours to minutes."""
        if self.duration.data is not None:
            hours = float(self.duration.data)
            rounded_hours = math.ceil(hours * 2) / 2
            obj.duration = int(rounded_hours * 60)

    def process(  # type: ignore[override]
        self, formdata: object = None, obj: object = None, **kwargs: object
    ) -> None:
        """Process form data, converting minutes to hours for display."""
        super().process(formdata, obj, **kwargs)  # type: ignore[arg-type]
        if formdata is None and obj is not None and hasattr(obj, 'duration'):
            duration_minutes = getattr(obj, 'duration', None)
            if duration_minutes is not None:
                self.duration.data = duration_minutes / 60.0

    def update_model(self, model: TranslatorTimeReport) -> None:
        """Update the time report model with form data."""
        assert self.duration.data is not None
        assert self.assignment_date.data is not None

        model.assignment_type = self.assignment_type.data or None

        hours = float(self.duration.data)
        rounded_hours = math.ceil(hours * 2) / 2
        model.duration = int(rounded_hours * 60)

        model.case_number = self.case_number.data or None
        model.assignment_date = self.assignment_date.data
        model.notes = self.notes.data or None

        hourly_rate = self.get_hourly_rate(model.translator)
        model.hourly_rate = hourly_rate

        surcharge_pct = self.calculate_surcharge()
        model.surcharge_percentage = surcharge_pct

        travel_comp = float(self.travel_distance.data or 0)
        model.travel_compensation = travel_comp

        duration_hours = model.duration / 60.0
        base = hourly_rate * duration_hours
        surcharge_amount = base * (surcharge_pct / 100)
        model.total_compensation = base + surcharge_amount + travel_comp
