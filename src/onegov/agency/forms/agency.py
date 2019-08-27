from cgi import FieldStorage
from io import BytesIO
from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import ExtendedAgency
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from sqlalchemy import func
from sqlalchemy import String
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators


class ExtendedAgencyForm(Form):
    """ Form to edit agencies. """

    title = StringField(
        label=_("Title"),
        validators=[
            validators.InputRequired()
        ],
    )

    portrait = TextAreaField(
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
            result['organigram_file'] = self.organigram.raw_data[-1].file
        return result

    def update_model(self, model):
        model.title = self.title.data
        model.portrait = self.portrait.data
        model.export_fields = self.export_fields.data
        if self.organigram.action == 'delete':
            del model.organigram
        if self.organigram.action == 'replace':
            if self.organigram.data:
                model.organigram_file = self.organigram.raw_data[-1].file
        if hasattr(self, 'is_hidden_from_public'):
            model.is_hidden_from_public = self.is_hidden_from_public.data

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
        if hasattr(self, 'is_hidden_from_public'):
            self.is_hidden_from_public.data = model.is_hidden_from_public

        self.reorder_export_fields()


class MoveAgencyForm(Form):
    """ Form to move an agency. """

    parent_id = ChosenSelectField(
        label=_("Destination"),
        choices=[],
        validators=[
            validators.InputRequired()
        ]
    )

    def on_request(self):
        self.request.include('common')
        self.request.include('chosen')

        self.parent_id.choices = self.request.session.query(
            ExtendedAgency.id.cast(String),
            ExtendedAgency.title
        ).order_by(func.unaccent(ExtendedAgency.title)).all()
        self.parent_id.choices.insert(
            0, ('root', self.request.translate(_("- Root -")))
        )

    def update_model(self, model):
        session = self.request.session
        agencies = ExtendedAgencyCollection(session)

        parent_id = None
        parent = None
        if self.parent_id.data.isdigit():
            parent_id = int(self.parent_id.data)
            parent = agencies.by_id(parent_id)
        model.name = agencies.get_unique_child_name(model.title, parent)
        model.parent_id = parent_id

    def apply_model(self, model):
        def remove(item):
            self.parent_id.choices.pop(
                self.parent_id.choices.index((str(item.id), item.title))
            )

        def remove_with_children(item):
            remove(item)
            for child in item.children:
                remove_with_children(child)

        if model.parent:
            remove(model.parent)
        else:
            self.parent_id.choices.pop(0)
        remove_with_children(model)
