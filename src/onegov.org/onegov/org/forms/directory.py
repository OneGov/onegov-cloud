from onegov.directory import DirectoryConfiguration
from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.core.utils import safe_format_keys
from wtforms import StringField, TextAreaField, validators


class DirectoryForm(Form):
    """ Form for directories. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        render_kw={'rows': 4})

    structure = TextAreaField(
        label=_("Definition"),
        validators=[
            validators.InputRequired(),
            ValidFormDefinition(require_email_field=False)
        ],
        render_kw={'rows': 32, 'data-editor': 'form'})

    title_format = StringField(
        label=_("Title Format"),
        validators=[validators.InputRequired()])

    lead_format = StringField(
        label=_("Lead Format"),
        validators=[validators.InputRequired()])

    content_fields = TextAreaField(
        label=_("Content Fields"),
        render_kw={'rows': 8})

    address_fields = TextAreaField(
        label=_("Address Fields"),
        render_kw={'rows': 8})

    keyword_fields = TextAreaField(
        label=_("Keyword Fields"),
        render_kw={'rows': 8})

    def extract_field_ids(self, field):
        for line in field.data.splitlines():
            line = line.strip()
            yield line

    @property
    def configuration(self):
        content_fields = list(self.extract_field_ids(self.content_fields))
        address_fields = list(self.extract_field_ids(self.address_fields))
        keyword_fields = list(self.extract_field_ids(self.keyword_fields))

        return DirectoryConfiguration(
            title=self.title_format.data,
            lead=self.lead_format.data,
            order=safe_format_keys(self.title_format.data),
            keywords=keyword_fields,
            searchable=content_fields + address_fields,
            display={
                'content': content_fields,
                'address': address_fields
            }
        )

    @configuration.setter
    def configuration(self, cfg):
        self.title_format.data = cfg.title
        self.lead_format.data = cfg.lead or ''
        self.content_fields.data = '\n'.join(cfg.display.get('content', ''))
        self.address_fields.data = '\n'.join(cfg.display.get('address', ''))
        self.keyword_fields.data = '\n'.join(cfg.keywords)

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude={'configuration'})
        obj.configuration = self.configuration

    def process_obj(self, obj):
        self.configuration = obj.configuration
