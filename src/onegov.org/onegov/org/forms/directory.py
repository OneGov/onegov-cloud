from cached_property import cached_property
from colour import Color
from onegov.core.utils import safe_format_keys
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryZipArchive
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import Form
from onegov.form import merge_forms
from onegov.form import parse_formcode
from onegov.form.errors import FormError
from onegov.form.fields import IconField
from onegov.form.fields import UploadField
from onegov.form.filters import as_float
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import ValidFormDefinition
from onegov.form.validators import WhitelistedMimeType
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import PaymentMethodForm
from onegov.org.theme.org_theme import user_options
from sqlalchemy.orm import object_session
from wtforms import BooleanField
from wtforms import DecimalField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import ValidationError
from wtforms import validators
from wtforms_components import ColorField


class DirectoryBaseForm(Form):
    """ Form for directories. """

    title = StringField(
        label=_("Title"),
        fieldset=_("General"),
        validators=[validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        fieldset=_("General"),
        description=_("Describes what this directory is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Further Information"),
        fieldset=_("General"))

    structure = TextAreaField(
        label=_("Definition"),
        fieldset=_("General"),
        validators=[
            validators.InputRequired(),
            ValidFormDefinition(require_email_field=False)
        ],
        render_kw={'rows': 32, 'data-editor': 'form'})

    enable_map = RadioField(
        label=_("Coordinates"),
        fieldset=_("General"),
        choices=[
            (
                'no',
                _("Entries have no coordinates")
            ),
            (
                'entry',
                _("Coordinates are shown on each entry")
            ),
            (
                'everywhere',
                _("Coordinates are shown on the directory and on each entry")
            ),
        ],
        default='everywhere')

    title_format = StringField(
        label=_("Title-Format"),
        fieldset=_("Display"),
        validators=[validators.InputRequired()],
        render_kw={'class_': 'formcode-format'})

    lead_format = StringField(
        label=_("Lead-Format"),
        fieldset=_("Display"),
        render_kw={'class_': 'formcode-format'})

    content_fields = TextAreaField(
        label=_("Main view"),
        fieldset=_("Display"),
        render_kw={'class_': 'formcode-select'})

    contact_fields = TextAreaField(
        label=_("Address"),
        fieldset=_("Display"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-exclude': 'fileinput,radio,checkbox'
        })

    keyword_fields = TextAreaField(
        label=_("Filters"),
        fieldset=_("Display"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'radio,checkbox'
        })

    thumbnail = TextAreaField(
        label=_("Thumbnail"),
        fieldset=_("Display"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'fileinput'
        }
    )

    marker_icon = IconField(
        label=_("Icon"),
        fieldset=_("Marker"),
    )

    marker_color_type = RadioField(
        label=_("Marker Color"),
        fieldset=_("Marker"),
        choices=[
            ('default', _("Default")),
            ('custom', _("Custom"))
        ],
        default='default'
    )

    marker_color_value = ColorField(
        label=_("Color"),
        fieldset=_("Marker"),
        depends_on=('marker_color_type', 'custom')
    )

    order = RadioField(
        label=_("Order"),
        fieldset=_("Order"),
        choices=[
            ('by-title', _("By title")),
            ('by-format', _("By format"))
        ],
        default='by-title')

    order_format = StringField(
        label=_("Order-Format"),
        fieldset=_("Order"),
        render_kw={'class_': 'formcode-format'},
        validators=[validators.InputRequired()],
        depends_on=('order', 'by-format'))

    order_direction = RadioField(
        label=_("Direction"),
        fieldset=_("Order"),
        choices=[
            ('asc', _("Ascending")),
            ('desc', _("Descending"))
        ],
        default='asc'
    )

    link_pattern = StringField(
        label=_("Pattern"),
        fieldset=_("External Link"),
        render_kw={'class_': 'formcode-format'},
    )

    link_title = StringField(
        label=_("Title"),
        fieldset=_("External Link")
    )

    link_visible = BooleanField(
        label=_("Visible"),
        fieldset=_("External Link"),
        default=True
    )

    enable_submissions = BooleanField(
        label=_("Users may propose new entries"),
        fieldset=_("New entries"),
        default=True)

    guideline = HtmlField(
        label=_("Guideline"),
        fieldset=_("New entries"),
        depends_on=('enable_submissions', 'y'))

    price = RadioField(
        label=_("Price"),
        fieldset=_("New entries"),
        choices=[
            ('free', _("Free of charge")),
            ('paid', _("Paid"))
        ],
        default='free',
        depends_on=('enable_submissions', 'y'))

    price_per_submission = DecimalField(
        label=_("Price per submission"),
        fieldset=_("New entries"),
        filters=(as_float, ),
        validators=[validators.Optional()],
        depends_on=('enable_submissions', 'y', 'price', 'paid'))

    currency = StringField(
        label=_("Currency"),
        fieldset=_("New entries"),
        default="CHF",
        depends_on=('enable_submissions', 'y', 'price', 'paid'),
        validators=[validators.InputRequired()])

    @cached_property
    def known_field_ids(self):
        try:
            return {
                field.id for field in
                flatten_fieldsets(parse_formcode(self.structure.data))
            }
        except FormError:
            return None

    @cached_property
    def missing_fields(self):
        try:
            return self.configuration.missing_fields(self.structure.data)
        except FormError:
            return None

    def extract_field_ids(self, field):
        if not self.known_field_ids:
            return

        for line in field.data.splitlines():
            line = line.strip()

            if as_internal_id(line) in self.known_field_ids:
                yield line

    def validate_title_format(self, field):
        if self.missing_fields and 'title' in self.missing_fields:
            raise ValidationError(
                _("The following fields are unknown: ${fields}", mapping={
                    'fields': ', '.join(self.missing_fields['title'])
                }))

    def validate_lead_format(self, field):
        if self.missing_fields and 'lead' in self.missing_fields:
            raise ValidationError(
                _("The following fields are unknown: ${fields}", mapping={
                    'fields': ', '.join(self.missing_fields['lead'])
                }))

    def validate_thumbnail(self, field):
        if field.data and '\n' in field.data:
            raise ValidationError(
                _("Please select at most one thumbnail field")
            )

    @property
    def default_marker_color(self):
        return self.request.app.org.theme_options.get('primary-color')\
            or user_options['primary-color']

    @property
    def marker_color(self):
        if self.marker_color_value.data:
            return self.marker_color_value.data.get_hex()

    @marker_color.setter
    def marker_color(self, value):
        self.marker_color_value.data = Color(
            value or self.default_marker_color)

    @property
    def configuration(self):
        content_fields = list(self.extract_field_ids(self.content_fields))
        contact_fields = list(self.extract_field_ids(self.contact_fields))
        keyword_fields = list(self.extract_field_ids(self.keyword_fields))

        order_format = self.data[
            self.order.data == 'by-title' and 'title_format' or 'order_format'
        ]

        return DirectoryConfiguration(
            title=self.title_format.data,
            lead=self.lead_format.data,
            order=safe_format_keys(order_format),
            keywords=keyword_fields,
            searchable=content_fields + contact_fields,
            display={
                'content': content_fields,
                'contact': contact_fields
            },
            direction=self.order_direction.data,
            link_pattern=self.link_pattern.data,
            link_title=self.link_title.data,
            link_visible=self.link_visible.data,
            thumbnail=self.thumbnail.data and self.thumbnail.data.split()[0]
        )

    @configuration.setter
    def configuration(self, cfg):
        self.title_format.data = cfg.title
        self.lead_format.data = cfg.lead or ''
        self.content_fields.data = '\n'.join(cfg.display.get('content', ''))
        self.contact_fields.data = '\n'.join(cfg.display.get('contact', ''))
        self.keyword_fields.data = '\n'.join(cfg.keywords)
        self.order_direction = cfg.direction == 'desc' and 'desc' or 'asc'
        self.link_pattern.data = cfg.link_pattern
        self.link_title.data = cfg.link_title
        self.link_visible.data = cfg.link_visible
        self.thumbnail.data = cfg.thumbnail

        if safe_format_keys(cfg.title) == cfg.order:
            self.order.data = 'by-title'
        else:
            self.order.data = 'by-format'
            self.order_format.data = ''.join(f'[{key}]' for key in cfg.order)

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude={'configuration'})
        obj.configuration = self.configuration

        if self.marker_color_type.data == 'default':
            obj.marker_color = None
        else:
            obj.marker_color = self.marker_color

    def process_obj(self, obj):
        self.configuration = obj.configuration

        if obj.marker_color:
            self.marker_color_type.data = 'custom'
            self.marker_color = obj.marker_color
        else:
            self.marker_color_type.data = 'default'
            self.marker_color = self.default_marker_color


class DirectoryForm(merge_forms(DirectoryBaseForm, PaymentMethodForm)):

    payment_method_args = PaymentMethodForm.payment_method.kwargs.copy()
    payment_method_args['fieldset'] = _("New entries")
    payment_method_args['depends_on'] = (
        'enable_submissions', 'y', 'price', 'paid')

    payment_method = RadioField(**payment_method_args)


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

        count = 0

        def count_entry(entry):
            nonlocal count
            count += 1

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
            apply_metadata=self.import_config.data == 'yes',
            after_import=count_entry
        )

        return count
