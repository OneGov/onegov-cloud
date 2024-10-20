from datetime import date, datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import PreviewField
from onegov.form.validators import If, ValidDateRange
from onegov.wtfs import _
from onegov.wtfs.fields import HintField
from onegov.wtfs.models import Municipality, ScanJob
from onegov.wtfs.models import PickupDate
from wtforms.fields import DateField
from wtforms.fields import HiddenField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, ValidationError
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from sedate import pytz, replace_timezone, utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.wtfs.collections import ScanJobCollection


def coerce_date(value: str | date | None) -> date | None:
    if isinstance(value, str):
        return parse(value).date()
    return value


class DispatchTimeValidator:
    """Ensures no scan jobs are submitted on the same day after 17:00"""

    def __init__(self, max_hour: int = 17):
        self.max_hour = max_hour
        self.timezone = 'Europe/Zurich'

    def __call__(self, form: Form, field: DateField) -> None:
        dispatch_date = field.data
        now = utcnow()

        if isinstance(dispatch_date, date):
            if dispatch_date != now.date():
                return

        if self.too_late_to_scan():
            raise ValidationError(
                _(
                    'Sorry, no scans are allowed after this time on the same '
                    'day.'
                )
            )

    def too_late_to_scan(self) -> bool:
        now = datetime.now(pytz.timezone(self.timezone))
        y, m, d = now.year, now.month, now.day
        max_hour_date = self.tzdatetime(y, m, d, hour=self.max_hour, minute=0)
        return now.time() > max_hour_date.time()

    def tzdatetime(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int
    ) -> datetime:
        """Returns the timezone-aware datetime"""
        return replace_timezone(
            datetime(year, month, day, hour, minute), self.timezone
        )


class AddScanJobForm(Form):

    type_hint1 = HintField(
        label='',
        macro='deadline_hint',
        depends_on=('type', 'normal')
    )

    type = RadioField(
        label=_('Type'),
        choices=[('normal', _('Regular shipment'))],
        validators=[InputRequired()],
        default='normal'
    )

    type_hint = HintField(
        label='',
        macro='express_shipment_hint',
        depends_on=('type', 'express')
    )

    dispatch_date_normal = SelectField(
        label=_('Dispatch date'),
        choices=[],
        depends_on=('type', 'normal'),
        validators=[InputRequired(), DispatchTimeValidator()],
        coerce=coerce_date
    )

    dispatch_date_express = DateField(
        label=_('Dispatch date'),
        depends_on=('type', 'express'),
        validators=[
            InputRequired(),
            ValidDateRange(
                min=relativedelta(days=0),
                message=_("Date can't be in the past.")
            )
        ],
        default=date.today
    )

    dispatch_boxes = IntegerField(
        label=_('Boxes'),
        fieldset=_('Dispatch to the tax office'),
        validators=[
            If(
                lambda form, field: form.type.data == 'normal',
                NumberRange(min=1)
            ),
            If(
                lambda form, field: form.type.data != 'normal',
                Optional(),
                NumberRange(min=0)
            ),
        ],
        render_kw={'size': 3, 'clear': False},
    )
    dispatch_tax_forms_older = IntegerField(
        label=_('Tax forms (older)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_('Tax forms (previous year)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_('Tax forms'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_single_documents = IntegerField(
        label=_('Single documents'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3},
    )
    dispatch_note = TextAreaField(
        label=_('Note'),
        fieldset=_('Dispatch to the tax office'),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_('Headquarters'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6, 'clear': False},
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_('Scan center'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6, 'clear': False},
    )

    @property
    def municipality_id(self) -> str | None:
        return self.request.identity.groupid or None  # type:ignore

    @property
    def dispatch_date(self) -> date:
        if self.type.data == 'express':
            assert self.dispatch_date_express.data is not None
            return self.dispatch_date_express.data
        return self.dispatch_date_normal.data

    def dispatch_dates(self, after: date) -> list[date]:
        query = self.request.session.query(PickupDate.date.label('date'))
        query = query.filter(
            PickupDate.municipality_id == self.municipality_id
        )
        query = query.filter(PickupDate.date > after)
        query = query.order_by(PickupDate.date)
        return [r.date for r in query] or [date(2018, 1, 1), date.today()]

    @property
    def return_date(self) -> date | None:
        if self.type.data == 'express':
            return None
        return self.dispatch_dates(self.dispatch_date)[0]

    def update_labels(self) -> None:
        year = date.today().year
        self.dispatch_tax_forms_older.label.text = _(
            'Tax forms until ${year}', mapping={'year': year - 2}
        )
        self.dispatch_tax_forms_last_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year - 1}
        )
        self.dispatch_tax_forms_current_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year}
        )

    def on_request(self) -> None:
        # Shipment types
        if self.request.has_role('editor'):
            self.type.choices = [
                ('normal', _('Regular shipment')),
                ('express', _('Express shipment'))
            ]

        # Dispatch dates
        self.dispatch_date_normal.choices = [
            (r, f'{r:%d.%m.%Y}') for r in self.dispatch_dates(date.today())
        ]

        # Labels
        self.update_labels()

    def update_model(self, model: ScanJob) -> None:
        model.municipality_id = self.request.identity.groupid  # type:ignore
        model.type = self.type.data
        model.dispatch_date = self.dispatch_date
        model.return_date = self.return_date
        for name in (
            'dispatch_boxes',
            'dispatch_tax_forms_current_year',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_older',
            'dispatch_single_documents',
            'dispatch_note',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ):
            setattr(model, name, getattr(self, name).data)


class EditScanJobForm(Form):

    callout = _("Fill in until 17.00 o'clock the evening before.")

    dispatch_boxes = IntegerField(
        label=_('Boxes'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3, 'clear': False},
    )
    dispatch_tax_forms_older = IntegerField(
        label=_('Tax forms (older)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_('Tax forms (previous year)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_('Tax forms'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_single_documents = IntegerField(
        label=_('Single documents'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3},
    )
    dispatch_note = TextAreaField(
        label=_('Note'),
        fieldset=_('Dispatch to the tax office'),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_('Headquarters'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6, 'clear': False},
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_('Scan center'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6},
    )

    def update_labels(self) -> None:
        year = self.model.dispatch_date.year
        self.dispatch_tax_forms_older.label.text = _(
            'Tax forms until ${year}', mapping={'year': year - 2}
        )
        self.dispatch_tax_forms_last_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year - 1}
        )
        self.dispatch_tax_forms_current_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year}
        )

    def on_request(self) -> None:
        self.update_labels()

    def update_model(self, model: ScanJob) -> None:
        for name in (
            'dispatch_boxes',
            'dispatch_tax_forms_current_year',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_older',
            'dispatch_single_documents',
            'dispatch_note',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ):
            setattr(model, name, getattr(self, name).data)

    def apply_model(self, model: ScanJob) -> None:
        for name in (
            'dispatch_boxes',
            'dispatch_tax_forms_current_year',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_older',
            'dispatch_single_documents',
            'dispatch_note',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ):
            getattr(self, name).data = getattr(model, name)

        self.callout = _(
            "Fill in until 17.00 o'clock the evening before ${date}.",
            mapping={'date': f'{model.dispatch_date:%d.%m.%Y}'}
        )


class UnrestrictedScanJobForm(Form):

    municipality_id = SelectField(
        label=_('Municipality'),
        choices=[],
        validators=[InputRequired()]
    )

    type = RadioField(
        label=_('Type'),
        choices=[
            ('normal', _('Regular shipment')),
            ('express', _('Express shipment'))
        ],
        validators=[InputRequired()],
        default='normal'
    )

    dispatch_date = DateField(
        label=_('Dispatch date'),
        validators=[InputRequired(), DispatchTimeValidator()],
        default=date.today,
    )

    dispatch_date_hint = PreviewField(
        label=_('Regular dispatch dates'),
        fields=('municipality_id',),
        events=('change',),
        url=lambda meta: meta.request.link(
            meta.request.app.principal,
            name='dispatch-dates'
        )
    )

    dispatch_boxes = IntegerField(
        label=_('Boxes'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3, 'clear': False},
    )
    dispatch_tax_forms_older = IntegerField(
        label=_('Tax forms (older)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_('Tax forms (previous year)'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_('Tax forms'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    dispatch_single_documents = IntegerField(
        label=_('Single documents'),
        fieldset=_('Dispatch to the tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3},
    )
    dispatch_note = TextAreaField(
        label=_('Note'),
        fieldset=_('Dispatch to the tax office'),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_('Headquarters'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6, 'clear': False},
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_('Scan center'),
        fieldset=_('Dispatch to the cantonal tax office'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 6},
    )

    return_date = DateField(
        label=_('Return date'),
        fieldset=_('Return to the municipality'),
        validators=[Optional()]
    )

    return_boxes = IntegerField(
        label=_('Boxes'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3, 'clear': False},
    )
    return_tax_forms_older = IntegerField(
        label=_('Tax forms (older)'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    return_tax_forms_last_year = IntegerField(
        label=_('Tax forms (previous year)'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    return_tax_forms_current_year = IntegerField(
        label=_('Tax forms'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    return_single_documents = IntegerField(
        label=_('Single documents'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3},

    )
    return_unscanned_tax_forms_older = IntegerField(
        label=_('Unscanned tax forms (older)'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'offset': 3, 'size': 2, 'clear': False},
    )
    return_unscanned_tax_forms_last_year = IntegerField(
        label=_('Unscanned tax forms (previous year)'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},
    )
    return_unscanned_tax_forms_current_year = IntegerField(
        label=_('Unscanned tax forms'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 2, 'clear': False},

    )
    return_unscanned_single_documents = IntegerField(
        label=_('Unscanned single documents'),
        fieldset=_('Return to the municipality'),
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'size': 3},
    )
    return_note = TextAreaField(
        label=_('Note'),
        fieldset=_('Return to the municipality'),
        render_kw={'rows': 5},
    )

    def update_labels(self) -> None:
        if isinstance(self.model, ScanJob):
            year = self.model.dispatch_date.year
        else:
            year = date.today().year

        self.dispatch_tax_forms_older.label.text = _(
            'Tax forms until ${year}', mapping={'year': year - 2}
        )
        self.dispatch_tax_forms_last_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year - 1}
        )
        self.dispatch_tax_forms_current_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year}
        )
        self.return_tax_forms_older.label.text = _(
            'Tax forms until ${year}', mapping={'year': year - 2}
        )
        self.return_tax_forms_last_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year - 1}
        )
        self.return_tax_forms_current_year.label.text = _(
            'Tax forms ${year}', mapping={'year': year}
        )
        self.return_unscanned_tax_forms_older.label.text = _(
            'Unscanned tax forms until ${year}', mapping={'year': year - 2}
        )
        self.return_unscanned_tax_forms_last_year.label.text = _(
            'Unscanned tax forms ${year}', mapping={'year': year - 1}
        )
        self.return_unscanned_tax_forms_current_year.label.text = _(
            'Unscanned tax forms ${year}', mapping={'year': year}
        )

    def on_request(self) -> None:
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number'),
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            (r.id.hex, f'{r.name} ({r.bfs_number})') for r in query
        ]

        self.update_labels()

    def update_model(self, model: ScanJob) -> None:
        for name in (
            'municipality_id',
            'type',
            'dispatch_date',
            'dispatch_boxes',
            'dispatch_tax_forms_current_year',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_older',
            'dispatch_single_documents',
            'dispatch_note',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
            'return_boxes',
            'return_tax_forms_current_year',
            'return_tax_forms_last_year',
            'return_tax_forms_older',
            'return_single_documents',
            'return_date',
            'return_unscanned_tax_forms_current_year',
            'return_unscanned_tax_forms_last_year',
            'return_unscanned_tax_forms_older',
            'return_unscanned_single_documents',
            'return_note',
        ):
            setattr(model, name, getattr(self, name).data)

    def apply_model(self, model: ScanJob) -> None:
        self.municipality_id.data = model.municipality_id.hex
        for name in (
            'type',
            'dispatch_date',
            'dispatch_boxes',
            'dispatch_tax_forms_current_year',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_older',
            'dispatch_single_documents',
            'dispatch_note',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
            'return_date',
            'return_boxes',
            'return_tax_forms_current_year',
            'return_tax_forms_last_year',
            'return_tax_forms_older',
            'return_single_documents',
            'return_unscanned_tax_forms_current_year',
            'return_unscanned_tax_forms_last_year',
            'return_unscanned_tax_forms_older',
            'return_unscanned_single_documents',
            'return_note',
        ):
            getattr(self, name).data = getattr(model, name)


class ScanJobsForm(Form):

    sort_by = HiddenField()
    sort_order = HiddenField()

    from_date = DateField(
        label=_('Start date'),
        fieldset=_('Filter')
    )

    to_date = DateField(
        label=_('End date'),
        fieldset=_('Filter')
    )

    type = MultiCheckboxField(
        label=_('Type'),
        fieldset=_('Filter'),
        choices=[
            ('normal', _('Regular shipment')),
            ('express', _('Express shipment'))
        ]
    )

    term = StringField(
        label=_('Term'),
        fieldset=_('Filter')
    )

    def on_request(self) -> None:
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name: str) -> None:
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model: 'ScanJobCollection') -> None:
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.type.data = model.type  # type:ignore[assignment]
        self.term.data = model.term
        self.sort_by.data = model.sort_by
        self.sort_order.data = model.sort_order

        # default unselected checkboxes to all choices
        self.select_all('type')


class UnrestrictedScanJobsForm(ScanJobsForm):

    municipality_id = ChosenSelectMultipleField(
        label=_('Municipality'),
        fieldset=_('Filter'),
        choices=[]
    )

    def on_request(self) -> None:
        super().on_request()
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            (r.id.hex, f'{r.name} ({r.bfs_number})') for r in query
        ]

    def apply_model(self, model: 'ScanJobCollection') -> None:
        super().apply_model(model)
        self.municipality_id.data = model.municipality_id  # type:ignore
