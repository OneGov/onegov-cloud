from cgi import FieldStorage
from io import BytesIO
from onegov.agency import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.fields import MultiCheckboxField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
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
            ('person.title', _("Person: Title")),
            ('person.last_name', _("Person: Last Name")),
            ('person.first_name', _("Person: First Name")),
            ('person.year', _("Person: Year")),
            ('person.academic_title', _("Person: Academic Title")),
            ('person.profession', _("Person: Profession")),
            ('person.address', _("Person: Address")),
            ('person.political_party', _("Person: Political Party")),
            ('person.phone', _("Person: Phone")),
            ('person.direct_phone', _("Person: Direct Phone")),
            # todo: postfix?
        ],
        default=['membership.title', 'person.title'],
        fieldset=_("PDF Export"),
    )

    # todo: hide from public?

    # todo: coordinates?

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

        self.reorder_export_fields()
