from cached_property import cached_property
from onegov.core.utils import safe_format_keys
from onegov.directory import DirectoryConfiguration
from onegov.form import Form, flatten_fieldsets, parse_formcode, as_internal_id
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from wtforms import StringField, TextAreaField, validators


class DirectoryForm(Form):
    """ Form for directories. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this directory is about"),
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
        validators=[validators.InputRequired()],
        render_kw={'class_': 'formcode-format'})

    lead_format = StringField(
        label=_("Lead Format"),
        render_kw={'class_': 'formcode-format'})

    content_fields = TextAreaField(
        label=_("Content Fields"),
        render_kw={'class_': 'formcode-select'})

    contact_fields = TextAreaField(
        label=_("Contact Fields"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-exclude': 'fileinput,radio,checkbox'
        })

    keyword_fields = TextAreaField(
        label=_("Keyword Fields"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'radio,checkbox'
        })

    @cached_property
    def known_field_ids(self):
        return {
            field.id for field in
            flatten_fieldsets(parse_formcode(self.structure.data))
        }

    def extract_field_ids(self, field):
        for line in field.data.splitlines():
            line = line.strip()

            if as_internal_id(line) in self.known_field_ids:
                yield line

    @property
    def configuration(self):
        content_fields = list(self.extract_field_ids(self.content_fields))
        contact_fields = list(self.extract_field_ids(self.contact_fields))
        keyword_fields = list(self.extract_field_ids(self.keyword_fields))

        return DirectoryConfiguration(
            title=self.title_format.data,
            lead=self.lead_format.data,
            order=safe_format_keys(self.title_format.data),
            keywords=keyword_fields,
            searchable=content_fields + contact_fields,
            display={
                'content': content_fields,
                'contact': contact_fields
            }
        )

    @configuration.setter
    def configuration(self, cfg):
        self.title_format.data = cfg.title
        self.lead_format.data = cfg.lead or ''
        self.content_fields.data = '\n'.join(cfg.display.get('content', ''))
        self.contact_fields.data = '\n'.join(cfg.display.get('contact', ''))
        self.keyword_fields.data = '\n'.join(cfg.keywords)

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude={'configuration'})
        obj.configuration = self.configuration

    def process_obj(self, obj):
        self.configuration = obj.configuration
