from datetime import date
from datetime import timedelta
from dateutil.parser import parse
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import PreviewField
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms_components import DateRange
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


def tomorrow():
    return date.today() + timedelta(days=1)


def coerce_date(value):
    if isinstance(value, str):
        return parse(value).date()
    return value


class AddScanJobForm(Form):

    type = RadioField(
        label=_("Type"),
        choices=[('normal', _("Regular shipment"))],
        validators=[InputRequired()],
        default='normal'
    )

    dispatch_date_normal = SelectField(
        label=_("Dispatch date"),
        choices=[],
        depends_on=('type', 'normal'),
        validators=[
            InputRequired(),
            DateRange(min=tomorrow, message=_("Date must be in the future."))
        ],
        coerce=coerce_date
    )

    dispatch_date_express = DateField(
        label=_("Dispatch date"),
        depends_on=('type', 'express'),
        validators=[
            InputRequired(),
            DateRange(min=tomorrow, message=_("Date must be in the future."))
        ],
        default=tomorrow
    )

    dispatch_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Dispatch to the tax office"),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_("Headquarters"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_("Scan center"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )

    @property
    def group_id(self):
        return self.request.identity.groupid

    @property
    def municipality_id(self):
        if not self.group_id:
            return
        query = self.request.session.query(Municipality)
        query = query.filter_by(group_id=self.group_id)
        return query.one().id

    @property
    def dispatch_date(self):
        if self.type.data == 'express':
            return self.dispatch_date_express.data
        return self.dispatch_date_normal.data

    def on_request(self):
        # Shipment types
        if self.request.has_role('editor'):
            self.type.choices = [
                ('normal', _("Regular shipment")),
                ('express', _("Express shipment"))
            ]

        # Dispatch dates
        query = self.request.session.query(PickupDate.date.label('date'))
        query = query.filter(
            PickupDate.municipality_id == self.municipality_id
        )
        query = query.filter(PickupDate.date > date.today())
        self.dispatch_date_normal.choices = [
            (r.date, f"{r.date:%d.%m.%Y}") for r in query
        ]

    def update_model(self, model):
        model.municipality_id = self.municipality_id
        model.group_id = self.group_id
        model.type = self.type.data
        model.dispatch_date = self.dispatch_date
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

    dispatch_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Dispatch to the tax office"),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_("Headquarters"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_("Scan center"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )

    return_date = DateField(
        label=_("Return date"),
        default=tomorrow,
        validators=[Optional()]
    )

    return_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_current_year = IntegerField(
        label=_("Unscanned tax forms"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_last_year = IntegerField(
        label=_("Unscanned tax forms (previous year)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_older = IntegerField(
        label=_("Unscanned tax forms (older)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_single_documents = IntegerField(
        label=_("Unscanned single documents"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Return to the municipality"),
        render_kw={'rows': 5},
    )

    def update_model(self, model):
        for name in (
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
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_older',
            'return_scanned_single_documents',
            'return_unscanned_tax_forms_current_year',
            'return_unscanned_tax_forms_last_year',
            'return_unscanned_tax_forms_older',
            'return_unscanned_single_documents',
            'return_note',
        ):
            setattr(model, name, getattr(self, name).data)

    def apply_model(self, model):
        for name in (
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
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_older',
            'return_scanned_single_documents',
            'return_unscanned_tax_forms_current_year',
            'return_unscanned_tax_forms_last_year',
            'return_unscanned_tax_forms_older',
            'return_unscanned_single_documents',
            'return_note',
        ):
            getattr(self, name).data = getattr(model, name)


class UnrestrictedAddScanJobForm(Form):

    municipality_id = SelectField(
        label=_("Municipality"),
        choices=[],
        validators=[InputRequired()]
    )

    type = RadioField(
        label=_("Type"),
        choices=[
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment"))
        ],
        validators=[InputRequired()],
        default='normal'
    )

    dispatch_date = DateField(
        label=_("Dispatch date"),
        validators=[
            InputRequired(),
            DateRange(min=tomorrow, message=_("Date must be in the future."))
        ],
        default=tomorrow
    )

    dispatch_date_hint = PreviewField(
        label=_("Regular dispatch dates"),
        fields=('municipality_id',),
        events=('change',),
        url=lambda meta: meta.request.link(
            meta.request.app.principal,
            name='dispatch-dates'
        )
    )

    dispatch_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Dispatch to the tax office"),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_("Headquarters"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_("Scan center"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )

    @property
    def group_id(self):
        session = self.request.session
        with session.no_autoflush:
            query = session.query(Municipality)
            query = query.filter_by(id=self.municipality_id.data)
            return query.one().group_id

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [(r.id.hex, r.name) for r in query]

    def update_model(self, model):
        model.group_id = self.group_id

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
        ):
            setattr(model, name, getattr(self, name).data)


class UnrestrictedEditScanJobForm(Form):

    municipality_id = SelectField(
        label=_("Municipality"),
        choices=[],
        validators=[InputRequired()]
    )

    type = RadioField(
        label=_("Type"),
        choices=[
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment"))
        ],
        validators=[InputRequired()],
        default='normal'
    )

    dispatch_date = DateField(
        label=_("Dispatch date"),
        validators=[InputRequired()],
        default=tomorrow
    )

    dispatch_date_hint = PreviewField(
        label=_("Regular dispatch dates"),
        fields=('municipality_id',),
        events=('change',),
        url=lambda meta: meta.request.link(
            meta.request.app.principal,
            name='dispatch-dates'
        )
    )

    dispatch_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Dispatch to the tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Dispatch to the tax office"),
        render_kw={'rows': 5},
    )

    dispatch_cantonal_tax_office = IntegerField(
        label=_("Headquarters"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )
    dispatch_cantonal_scan_center = IntegerField(
        label=_("Scan center"),
        fieldset=_("Dispatch to the cantonal tax office"),
        validators=[Optional(), NumberRange(min=0)]
    )

    return_date = DateField(
        label=_("Return date"),
        default=tomorrow,
        validators=[Optional()]
    )

    return_boxes = IntegerField(
        label=_("Boxes"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_current_year = IntegerField(
        label=_("Tax forms"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_last_year = IntegerField(
        label=_("Tax forms (previous year)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_tax_forms_older = IntegerField(
        label=_("Tax forms (older)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_scanned_single_documents = IntegerField(
        label=_("Single documents"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_current_year = IntegerField(
        label=_("Unscanned tax forms"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_last_year = IntegerField(
        label=_("Unscanned tax forms (previous year)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_tax_forms_older = IntegerField(
        label=_("Unscanned tax forms (older)"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_unscanned_single_documents = IntegerField(
        label=_("Unscanned single documents"),
        fieldset=_("Return to the municipality"),
        validators=[Optional(), NumberRange(min=0)]

    )
    return_note = TextAreaField(
        label=_("Note"),
        fieldset=_("Return to the municipality"),
        render_kw={'rows': 5},
    )

    @property
    def group_id(self):
        session = self.request.session
        with session.no_autoflush:
            query = session.query(Municipality)
            query = query.filter_by(id=self.municipality_id.data)
            return query.one().group_id

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [(r.id.hex, r.name) for r in query]

    def update_model(self, model):
        model.group_id = self.group_id
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
            'return_date',
            'return_boxes',
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_older',
            'return_scanned_single_documents',
            'return_unscanned_tax_forms_current_year',
            'return_unscanned_tax_forms_last_year',
            'return_unscanned_tax_forms_older',
            'return_unscanned_single_documents',
            'return_note',
        ):
            setattr(model, name, getattr(self, name).data)

    def apply_model(self, model):
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
            'return_scanned_tax_forms_current_year',
            'return_scanned_tax_forms_last_year',
            'return_scanned_tax_forms_older',
            'return_scanned_single_documents',
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
        label=_("Start date"),
        fieldset=_("Filter")
    )

    to_date = DateField(
        label=_("End date"),
        fieldset=_("Filter")
    )

    type = MultiCheckboxField(
        label=_("Type"),
        fieldset=_("Filter"),
        choices=[
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment"))
        ]
    )

    term = StringField(
        label=_("Term"),
        fieldset=_("Filter")
    )

    def on_request(self):
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def apply_model(self, model):
        self.from_date.data = model.from_date
        self.to_date.data = model.to_date
        self.type.data = model.type
        self.term.data = model.term
        self.sort_by.data = model.sort_by
        self.sort_order.data = model.sort_order

        # default unselected checkboxes to all choices
        self.select_all('type')


class UnrestrictedScanJobsForm(ScanJobsForm):

    municipality_id = ChosenSelectMultipleField(
        label=_("Municipality"),
        fieldset=_("Filter")
    )

    def on_request(self):
        super().on_request()
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [(r.id.hex, r.name) for r in query]

    def apply_model(self, model):
        super().apply_model(model)
        self.municipality_id.data = model.municipality_id
