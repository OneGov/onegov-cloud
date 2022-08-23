from cgi import FieldStorage
from io import BytesIO
from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import ExtendedAgency
from onegov.agency.utils import handle_empty_p_tags
from onegov.core.security import Private
from onegov.core.utils import linkify
from onegov.form import Form
from onegov.form.fields import ChosenSelectField, HtmlField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import CoordinatesField
from sqlalchemy import func
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class ExtendedAgencyForm(Form):
    """ Form to edit agencies. """

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ],
    )

    portrait = HtmlField(
        label=_("Portrait"),
        render_kw={'rows': 10}
    )

    organigram = UploadField(
        label=_("Organigram"),
        validators=[
            WhitelistedMimeType({
                'image/jpeg',
                'image/png',
            }),
            FileSizeLimit(1 * 1024 * 1024)
        ]
    )

    coordinates = CoordinatesField(
        label=_('Location'),
        description=_(
            'Search for the exact address to set a marker. The address '
            'fields beneath are filled out automatically.'
        ),
        fieldset=_("Address"),
        render_kw={'data-map-type': 'marker'},
    )

    address = StringField(
        label=_('Street and house number'),
        fieldset=_("Address"),
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_("Address"),
    )

    city = StringField(
        label=_('City'),
        fieldset=_("Address"),
    )

    export_fields = MultiCheckboxField(
        label=_("Fields to include for each membership"),
        choices=[
            ('membership.title', _("Membership: Title")),
            ('membership.since', _("Membership: Since")),
            ('membership.addition', _("Membership: Addition")),
            ('person.title', _("Person: Title")),
            ('person.function', _("Person: Function")),
            ('person.last_name', _("Person: Last Name")),
            ('person.first_name', _("Person: First Name")),
            ('person.born', _("Person: Born")),
            ('person.academic_title', _("Person: Academic Title")),
            ('person.profession', _("Person: Profession")),
            ('person.address', _("Person: Address")),
            ('person.political_party', _("Person: Political Party")),
            ('person.parliamentary_group', _("Person: Parliamentary Group")),
            ('person.phone', _("Person: Phone")),
            ('person.phone_direct', _("Person: Direct Phone")),
        ],
        default=['membership.title', 'person.title'],
        fieldset=_("PDF Export"),
        render_kw={'class_': 'sortable-multi-checkbox'}
    )

    def on_request(self):
        self.request.include('sortable-multi-checkbox')

    def get_useful_data(self):
        exclude = {'csrf_token', 'organigram'}
        result = super(ExtendedAgencyForm, self).get_useful_data(exclude)
        if self.organigram.data:
            result['organigram_file'] = self.organigram.file
        if self.portrait.data:
            result['portrait'] = linkify(self.portrait.data, escape=False)
        return result

    def update_model(self, model):
        model.title = self.title.data
        model.portrait = handle_empty_p_tags(
            linkify(self.portrait.data, escape=False)
        )
        model.export_fields = self.export_fields.data
        if self.organigram.action == 'delete':
            del model.organigram
        if self.organigram.action == 'replace':
            if self.organigram.data:
                model.organigram_file = self.organigram.file
        model.address = self.address.data
        model.zip_code = self.zip_code.data
        model.city = self.city.data
        model.coordinates = self.coordinates.data
        if hasattr(self, 'access'):
            model.access = self.access.data
        if hasattr(self, 'publication_start'):
            model.publication_start = self.publication_start.data
        if hasattr(self, 'publication_end'):
            model.publication_end = self.publication_end.data

    def reorder_export_fields(self):
        titles = dict(self.export_fields.choices)
        self.export_fields.choices = [
            (choice, titles[choice]) for choice in self.export_fields.data
        ] + [
            choice for choice in self.export_fields.choices
            if choice[0] not in self.export_fields.data
        ]

    def apply_model(self, model):
        self.title.data = model.title
        self.portrait.data = model.portrait
        self.export_fields.data = model.export_fields
        if model.organigram_file:
            fs = FieldStorage()
            fs.file = BytesIO(model.organigram_file.read())
            fs.type = model.organigram_file.content_type
            fs.filename = model.organigram_file.filename
            self.organigram.data = self.organigram.process_fieldstorage(fs)
        self.address.data = model.address
        self.zip_code.data = model.zip_code
        self.city.data = model.city
        self.coordinates.data = model.coordinates
        if hasattr(self, 'access'):
            self.access.data = model.access
        if hasattr(self, 'publication_start'):
            self.publication_start.process_data(model.publication_start)
        if hasattr(self, 'publication_end'):
            self.publication_end.process_data(model.publication_end)

        self.reorder_export_fields()


class MoveAgencyForm(Form):
    """ Form to move an agency. """

    parent_id = ChosenSelectField(
        label=_("Destination"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        self.request.include('common')
        self.request.include('chosen')

        agencies = ExtendedAgencyCollection(self.request.session)
        self.parent_id.choices = [
            (str(agency.id), agency.title)
            for agency in agencies.query().order_by(None).order_by(
                func.unaccent(ExtendedAgency.title)
            )
            if self.request.has_permission(agency, Private)
        ]
        if self.request.has_permission(agencies, Private):
            self.parent_id.choices.insert(
                0, ('root', self.request.translate(_("- Root -")))
            )

    def update_model(self, model):
        session = self.request.session
        agencies = ExtendedAgencyCollection(session)

        parent_id = None
        parent = None
        if self.parent_id.data and self.parent_id.data.isdigit():
            parent_id = int(self.parent_id.data)
            parent = agencies.by_id(parent_id)
        model.name = agencies.get_unique_child_name(model.title, parent)
        model.parent_id = parent_id

    def apply_model(self, model):
        def remove(item):
            item = (str(item.id), item.title)
            if item in self.parent_id.choices:
                self.parent_id.choices.remove(item)

        def remove_with_children(item):
            remove(item)
            for child in item.children:
                remove_with_children(child)

        if model.parent:
            remove(model.parent)
        else:
            self.parent_id.choices.pop(0)
        remove_with_children(model)
