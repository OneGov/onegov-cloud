from datetime import date
from datetime import timedelta
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


def tomorrow():
    return date.today() + timedelta(days=1)


class AddScanJobForm(Form):

    municipality_id = ChosenSelectField(
        label=_("Municipality"),
        choices=[],
        validators=[InputRequired()]
    )

    type = RadioField(
        label=_("Type"),
        choices=[('normal', _("Regular shipment"))],
        validators=[InputRequired()],
        default='normal'
    )

    dispatch_date = SelectField(
        label=_("Dispatch date"),
        choices=[],
        depends_on=('type', 'normal'),
        validators=[InputRequired()]
    )

    dispatch_date_express = DateField(
        label=_("Dispatch date"),
        depends_on=('type', 'express'),
        validators=[InputRequired()],
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

    def set_municipality_id_choices(self, group_id=None):
        """ Queries and sets the list of municipalities for the given group
        or all groups.

        """
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name')
        )
        if group_id:
            query = query.filter(Municipality.group_id == group_id)
        query = query.order_by(Municipality.name)
        self.municipality_id.choices = [(r.id.hex, r.name) for r in query]

    def set_dispatch_date_choices(self, municipality_id=None):
        """ Queries and sets the dispatch dates for the given municipality or
        the first selectable municipality.

        """
        if municipality_id is None:
            choices = self.municipality_id.choices
            if not choices or not choices[0]:
                self.dispatch_date.choices = []
                return
            municipality_id = choices[0][0]

        query = self.request.session.query(PickupDate.date.label('date'))
        query = query.filter(PickupDate.municipality_id == municipality_id)
        query = query.filter(PickupDate.date > date.today())
        self.dispatch_date.choices = [
            (r.date.isoformat(), f"{r.date:%d.%m.%Y}") for r in query
        ]

    def on_request(self):
        if self.request.has_role('editor'):
            self.type.choices = [
                ('normal', _("Regular shipment")),
                ('express', _("Express shipment"))
            ]

        self.set_municipality_id_choices(self.request.identity.groupid)
        self.set_dispatch_date_choices()

    def update_model(self, model):
        model.municipality_id = self.municipality_id.data
        model.group_id = self.request.identity.groupid
        model.type = self.type.data
        model.dispatch_date = (
            self.dispatch_date_express.data if self.type.data == 'express' else
            self.dispatch_date.data
        )
        model.dispatch_boxes = self.dispatch_boxes.data
        model.dispatch_tax_forms_current_year = \
            self.dispatch_tax_forms_current_year.data
        model.dispatch_tax_forms_last_year = \
            self.dispatch_tax_forms_last_year.data
        model.dispatch_tax_forms_older = self.dispatch_tax_forms_older.data
        model.dispatch_single_documents = self.dispatch_single_documents.data
        model.dispatch_note = self.dispatch_note.data
        model.dispatch_cantonal_tax_office = \
            self.dispatch_cantonal_tax_office.data
        model.dispatch_cantonal_scan_center = \
            self.dispatch_cantonal_scan_center.data


class EditScanJobForm(AddScanJobForm):

    return_date = DateField(
        label=_("Return date"),
        default=tomorrow
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
        super().update_model(model)
        model.return_date = self.return_date.data
        model.return_boxes = self.return_boxes.data
        model.return_scanned_tax_forms_current_year = \
            self.return_scanned_tax_forms_current_year.data
        model.return_scanned_tax_forms_last_year = \
            self.return_scanned_tax_forms_last_year.data
        model.return_scanned_tax_forms_older = \
            self.return_scanned_tax_forms_older.data
        model.return_scanned_single_documents = \
            self.return_scanned_single_documents.data
        model.return_unscanned_tax_forms_current_year = \
            self.return_unscanned_tax_forms_current_year.data
        model.return_unscanned_tax_forms_last_year = \
            self.return_unscanned_tax_forms_last_year.data
        model.return_unscanned_tax_forms_older = \
            self.return_unscanned_tax_forms_older.data
        model.return_unscanned_single_documents = \
            self.return_unscanned_single_documents.data
        model.return_note = self.return_note.data

    def apply_model(self, model):
        self.municipality_id.data = model.municipality_id.hex
        self.type.data = model.type
        self.dispatch_date.data = model.dispatch_date
        self.dispatch_date_express.data = model.dispatch_date
        self.dispatch_boxes.data = model.dispatch_boxes
        self.dispatch_tax_forms_current_year.data = \
            model.dispatch_tax_forms_current_year
        self.dispatch_tax_forms_last_year.data = \
            model.dispatch_tax_forms_last_year
        self.dispatch_tax_forms_older.data = model.dispatch_tax_forms_older
        self.dispatch_single_documents.data = model.dispatch_single_documents
        self.dispatch_note.data = model.dispatch_note
        self.dispatch_cantonal_tax_office.data = \
            model.dispatch_cantonal_tax_office
        self.dispatch_cantonal_scan_center.data = \
            model.dispatch_cantonal_scan_center
        self.return_date.data = model.return_date
        self.return_boxes.data = model.return_boxes
        self.return_scanned_tax_forms_current_year.data = \
            model.return_scanned_tax_forms_current_year
        self.return_scanned_tax_forms_last_year.data = \
            model.return_scanned_tax_forms_last_year
        self.return_scanned_tax_forms_older.data = \
            model.return_scanned_tax_forms_older
        self.return_scanned_single_documents.data = \
            model.return_scanned_single_documents
        self.return_unscanned_tax_forms_current_year.data = \
            model.return_unscanned_tax_forms_current_year
        self.return_unscanned_tax_forms_last_year.data = \
            model.return_unscanned_tax_forms_last_year
        self.return_unscanned_tax_forms_older.data = \
            model.return_unscanned_tax_forms_older
        self.return_unscanned_single_documents.data = \
            model.return_unscanned_single_documents
        self.return_note.data = model.return_note


class UnrestrictedAddScanJobForm(AddScanJobForm):

    def on_request(self):
        self.type.choices = [
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment"))
        ]
        self.set_municipality_id_choices()
        self.set_dispatch_date_choices()

    def update_model(self, model):
        super().update_model(model)

        session = self.request.session
        with session.no_autoflush:
            query = session.query(Municipality)
            query = query.filter_by(id=self.municipality_id.data)
            model.group_id = query.one().group_id


class UnrestrictedEditScanJobForm(EditScanJobForm):

    def on_request(self):
        self.type.choices = [
            ('normal', _("Regular shipment")),
            ('express', _("Express shipment"))
        ]
        self.set_municipality_id_choices()
        self.set_dispatch_date_choices()

    def apply_model(self, model):
        super().apply_model(model)
        self.set_dispatch_date_choices(self.municipality_id.data)

    def update_model(self, model):
        super().update_model(model)

        session = self.request.session
        with session.no_autoflush:
            query = session.query(Municipality)
            query = query.filter_by(id=self.municipality_id.data)
            model.group_id = query.one().group_id
