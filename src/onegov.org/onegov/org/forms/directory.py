from cached_property import cached_property
from onegov.core.utils import safe_format_keys
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryZipArchive
from onegov.form import Form, flatten_fieldsets, parse_formcode, as_internal_id
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import ValidFormDefinition
from onegov.form.validators import WhitelistedMimeType
from onegov.org import _
from sqlalchemy.orm import object_session
from wtforms import BooleanField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import ValidationError
from wtforms import validators


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
        label=_("Title-Format"),
        validators=[validators.InputRequired()],
        render_kw={'class_': 'formcode-format'})

    lead_format = StringField(
        label=_("Lead-Format"),
        render_kw={'class_': 'formcode-format'})

    content_fields = TextAreaField(
        label=_("Main view"),
        render_kw={'class_': 'formcode-select'})

    contact_fields = TextAreaField(
        label=_("Address"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-exclude': 'fileinput,radio,checkbox'
        })

    keyword_fields = TextAreaField(
        label=_("Filters"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'radio,checkbox'
        })

    enable_map = BooleanField(
        label=_("Directory entries may have coordinates"),
        default=True
    )

    @cached_property
    def known_field_ids(self):
        return {
            field.id for field in
            flatten_fieldsets(parse_formcode(self.structure.data))
        }

    @cached_property
    def missing_fields(self):
        return self.configuration.missing_fields(self.structure.data)

    def extract_field_ids(self, field):
        for line in field.data.splitlines():
            line = line.strip()

            if as_internal_id(line) in self.known_field_ids:
                yield line

    def validate_title_format(self, field):
        if 'title' in self.missing_fields:
            raise ValidationError(
                _("The following fields are unknown: ${fields}", mapping={
                    'fields': ', '.join(self.missing_fields['title'])
                }))

    def validate_lead_format(self, field):
        if 'lead' in self.missing_fields:
            raise ValidationError(
                _("The following fields are unknown: ${fields}", mapping={
                    'fields': ', '.join(self.missing_fields['lead'])
                }))

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


class DirectoryImportForm(Form):

    import_config = RadioField(
        label=_("Apply directory configuration"),
        choices=(
            ('yes', _("Yes, import configuration and entries")),
            ('no', _("No, only import entries"))
        ),
        default='no',
        validators=[validators.InputRequired()]
    )

    mode = RadioField(
        label=_("Mode"),
        choices=(
            ('new', _("Only import new entries")),
            ('replace', _("Replace all entries")),
        ),
        default='new',
        validators=[validators.InputRequired()]
    )

    zip_file = UploadField(
        label=_("Import"),
        validators=[
            validators.DataRequired(),
            WhitelistedMimeType({
                'application/zip',
                'application/octet-stream'
            }),
            FileSizeLimit(25 * 1024 * 1024)
        ],
        render_kw=dict(force_simple=True)
    )

    def run_import(self, target):
        session = object_session(target)

        if self.mode.data == 'replace':
            for existing in target.entries:
                session.delete(existing)

            target.entries.clear()
            session.flush()

        archive = DirectoryZipArchive.from_buffer(self.zip_file.file)
        archive.read(
            target=target,
            skip_existing=True,
            limit=100,
            apply_metadata=self.import_config.data == 'yes'
        )
