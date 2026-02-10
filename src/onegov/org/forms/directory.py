from __future__ import annotations

from functools import cached_property

from wtforms import EmailField
from onegov.core.utils import safe_format_keys, normalize_for_url
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryZipArchive
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import Form
from onegov.form import merge_forms
from onegov.form import move_fields
from onegov.form import parse_formcode
from onegov.form.errors import FormError
from onegov.form.fields import ColorField
from onegov.form.fields import IconField, MultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.filters import as_float
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import PaymentForm, ChangeAdjacencyListUrlForm
from onegov.org.theme.org_theme import user_options
from sqlalchemy.orm import object_session
from wtforms.fields import BooleanField
from wtforms.fields import DecimalField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import Email
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.form.parser.core import ParsedField
    from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Session
    from wtforms import Field


class DirectoryBaseForm(Form):
    """ Form for directories. """

    if TYPE_CHECKING:
        request: OrgRequest

    title = StringField(
        label=_('Title'),
        fieldset=_('General'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        fieldset=_('General'),
        description=_('Describes what this directory is about'),
        render_kw={'rows': 4})

    title_further_information = StringField(
        label=_('Title'),
        fieldset=_('Further Information'),
        description=_(
            'If left empty "Further Information" will be used as title')
    )

    text = HtmlField(
        label=_('Text'),
        fieldset=_('Further Information'))

    position = RadioField(
        label=_('Position'),
        fieldset=_('Further Information'),
        choices=[
            ('above', _('Above the entries')),
            ('below', _('Below the entries'))
        ],
        default='below'
    )

    structure = TextAreaField(
        label=_('Definition'),
        fieldset=_('General'),
        validators=[
            InputRequired(),
            ValidFormDefinition(
                require_email_field=False,
                require_title_fields=True
            )
        ],
        render_kw={'rows': 32, 'data-editor': 'form'})

    enable_map = RadioField(
        label=_('Coordinates'),
        fieldset=_('General'),
        choices=[
            (
                'no',
                _('Entries have no coordinates')
            ),
            (
                'entry',
                _('Coordinates are shown on each entry')
            ),
            (
                'everywhere',
                _('Coordinates are shown on the directory and on each entry')
            ),
        ],
        default='everywhere')

    title_format = StringField(
        label=_('Title-Format'),
        fieldset=_('Display'),
        validators=[InputRequired()],
        render_kw={'class_': 'formcode-format'})

    lead_format = StringField(
        label=_('Lead-Format'),
        fieldset=_('Display'),
        render_kw={'class_': 'formcode-format'})

    empty_notice = StringField(
        label=_('Empty Directory Notice'),
        fieldset=_('Display'),
        description=_(
            'This text will be displayed when the directory '
            'contains no (visible) entries. When left empty '
            'a generic default text will be shown instead.'
        ))

    numbering = RadioField(
        label=_('Numbering'),
        fieldset=_('Display'),
        choices=[
            ('none', _('None')),
            ('standard', _('Standard')),
            ('custom', _('Custom'))
        ],
        default='none')

    numbers = TextAreaField(
        label=_('Custom Numbering'),
        fieldset=_('Display'),
        depends_on=('numbering', 'custom'),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'integer_range'
        })

    content_fields = TextAreaField(
        label=_('Main view'),
        fieldset=_('Display'),
        render_kw={'class_': 'formcode-select'})

    content_hide_labels = TextAreaField(
        label=_('Hide these labels on the main view'),
        fieldset=_('Display'),
        render_kw={'class_': 'formcode-select'})

    contact_fields = TextAreaField(
        label=_('Contact Information Sidebar'),
        fieldset=_('Display'),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-exclude': 'fileinput,radio,checkbox',
            'long_description':
                _('The contact information is displayed in the sidebar '
                  'without field names.')
        })

    keyword_fields = TextAreaField(
        label=_('Filters'),
        fieldset=_('Display'),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'radio,checkbox'
        })

    thumbnail = TextAreaField(
        label=_('Thumbnail'),
        fieldset=_('Display'),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'fileinput'
        })

    show_as_thumbnails = TextAreaField(
        label=_('Pictures to be displayed as thumbnails on an entry'),
        fieldset=_('Display'),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'fileinput'
        })

    overview_two_columns = BooleanField(
        label=_('Overview layout with tiles'),
        fieldset=_('Display'),
        default=False)

    address_block_title_type = RadioField(
        label=_('Address Block Title'),
        fieldset=_('Address Block'),
        default='auto',
        choices=(
            ('auto', _('The first line of the address')),
            ('fixed', _('Static title')),
        )
    )

    address_block_title = StringField(
        label=_('Title'),
        fieldset=_('Address Block'),
        depends_on=('address_block_title_type', 'fixed'),
    )

    marker_icon = IconField(
        label=_('Icon'),
        fieldset=_('Marker'))

    marker_color_type = RadioField(
        label=_('Marker Color'),
        fieldset=_('Marker'),
        choices=[
            ('default', _('Default')),
            ('custom', _('Custom'))
        ],
        default='default')

    marker_color_value = ColorField(
        label=_('Color'),
        fieldset=_('Marker'),
        depends_on=('marker_color_type', 'custom'))

    order = RadioField(
        label=_('Order'),
        fieldset=_('Order'),
        choices=[
            ('by-title', _('By title')),
            ('by-format', _('By format'))
        ],
        default='by-title')

    order_format = StringField(
        label=_('Order-Format'),
        fieldset=_('Order'),
        render_kw={'class_': 'formcode-format'},
        validators=[InputRequired()],
        depends_on=('order', 'by-format'))

    order_direction = RadioField(
        label=_('Direction'),
        fieldset=_('Order'),
        choices=[
            ('asc', _('Ascending')),
            ('desc', _('Descending'))
        ],
        default='asc')

    link_pattern = StringField(
        label=_('Pattern'),
        fieldset=_('External Link'),
        render_kw={'class_': 'formcode-format'})

    link_title = StringField(
        label=_('Title'),
        fieldset=_('External Link'))

    link_visible = BooleanField(
        label=_('Visible'),
        fieldset=_('External Link'),
        default=True)

    enable_submissions = BooleanField(
        label=_('Users may propose new entries'),
        fieldset=_('New entries'),
        default=False)

    submissions_guideline = HtmlField(
        label=_('Guideline'),
        fieldset=_('New entries'),
        depends_on=('enable_submissions', 'y'))

    price = RadioField(
        label=_('Price'),
        fieldset=_('New entries'),
        choices=[
            ('free', _('Free of charge')),
            ('paid', _('Paid'))
        ],
        default='free',
        depends_on=('enable_submissions', 'y'))

    price_per_submission = DecimalField(
        label=_('Price per submission'),
        fieldset=_('New entries'),
        filters=(as_float, ),
        validators=[Optional()],
        depends_on=('enable_submissions', 'y', 'price', 'paid'))

    currency = StringField(
        label=_('Currency'),
        fieldset=_('New entries'),
        default='CHF',
        depends_on=('enable_submissions', 'y', 'price', 'paid'),
        validators=[InputRequired()])

    enable_change_requests = BooleanField(
        label=_('Users may send change requests'),
        fieldset=_('Change requests'),
        default=False)

    change_requests_guideline = HtmlField(
        label=_('Guideline'),
        fieldset=_('Change requests'),
        depends_on=('enable_change_requests', 'y'))

    enable_publication = BooleanField(
        label=_('Enable publication dates'),
        description=_('Users may suggest publication start and/or end '
                      'of the entry on submissions and change requests'),
        fieldset=_('Publication'),
        default=False)

    required_publication = BooleanField(
        label=_('Required publication dates'),
        fieldset=_('Publication'),
        depends_on=('enable_publication', 'y'),
        default=False)

    enable_update_notifications = BooleanField(
        label=_('Enable registering for update notifications'),
        description=_('Users can register for updates on new entries'),
        fieldset=_('Notifications'),
        default=False)

    submitter_meta_fields = MultiCheckboxField(
        label=_('Information to be provided in addition to the E-mail'),
        choices=(
            ('submitter_name', _('Name')),
            ('submitter_address', _('Address')),
            ('submitter_phone', _('Phone')),
        ),
        fieldset=_('Submitter')
    )

    layout = RadioField(
        label=_('Layout'),
        fieldset=_('Layout'),
        choices=[
            ('default', _('Default')),
            ('accordion', _('Accordion')),
        ],
        default='default')

    @cached_property
    def known_field_ids(self) -> set[str] | None:
        # FIXME: We should probably define this in relation to known_fields
        #        so we don't parse the form twice if we access both properties
        try:
            return {
                field.id for field in
                flatten_fieldsets(parse_formcode(self.structure.data))
            }
        except FormError:
            return None

    @cached_property
    def known_fields(self) -> list[ParsedField] | None:
        try:
            return list(
                flatten_fieldsets(parse_formcode(self.structure.data))
            )
        except FormError:
            return None

    @cached_property
    def missing_fields(self) -> dict[str, list[str]] | None:
        try:
            return self.configuration.missing_fields(self.structure.data)
        except FormError:
            return None

    def extract_field_ids(self, field: Field) -> Iterator[str]:
        if not self.known_field_ids:
            return

        for line in field.data.splitlines():
            line = line.strip()

            if as_internal_id(line) in self.known_field_ids:
                yield line

    def validate_title_format(self, field: Field) -> None:
        if self.missing_fields and 'title' in self.missing_fields:
            raise ValidationError(
                _('The following fields are unknown: ${fields}', mapping={
                    'fields': ', '.join(self.missing_fields['title'])
                }))

    def validate_lead_format(self, field: Field) -> None:
        if self.missing_fields and 'lead' in self.missing_fields:
            raise ValidationError(
                _('The following fields are unknown: ${fields}', mapping={
                    'fields': ', '.join(self.missing_fields['lead'])
                }))

    def validate_thumbnail(self, field: Field) -> None:
        if field.data and '\n' in field.data:
            raise ValidationError(
                _('Please select at most one thumbnail field')
            )

    def validate_numbers(self, field: Field) -> None:
        if self.numbering.data == 'custom' and (
            '\n' in field.data or field.data == ''
        ):
            raise ValidationError(
                _('Please select exactly one numbering field')
            )

    def ensure_public_fields_for_submissions(self) -> bool | None:
        """ Force directories to show all fields (no hidden fields) if the
        user may send in new entries or update exsting ones.

        Otherwise we would have to filter out private fields which presents
        all kinds of edge-cases that we should probably not solve - directories
        are not meant to be private repositories.

        """
        inputs = (
            self.enable_change_requests,
            self.enable_submissions
        )

        if not any(i.data for i in inputs):
            return None

        hidden = self.first_hidden_field(self.configuration)

        if hidden:
            msg = _(
                'User submissions are not possible, because «${field}» '
                'is not visible. Only if all fields are visible are user '
                'submission possible - otherwise users may see data that '
                'they are not intended to see. ', mapping={
                    'field': hidden.label
                }
            )

            for i in inputs:
                if i.data:
                    assert isinstance(i.errors, list)
                    i.errors.append(msg)

            return False
        return None

    def first_hidden_field(
        self,
        configuration: DirectoryConfiguration
    ) -> ParsedField | None:
        """ Returns the first hidden field, or None. """

        for field in flatten_fieldsets(parse_formcode(self.structure.data)):
            if not self.is_public(field.id, configuration):
                return field
        return None

    def is_public(
        self,
        fid: str,
        configuration: DirectoryConfiguration
    ) -> bool:
        """ Returns true if the given field id is public.

        A field is public, if none of these are true:

            * It is part of the title/lead
            * It is part of the display
            * It is part of the keywords
            * It is used as the thumbnail

        Though we might also glean other fields if they are simply searchable
        or if they are part of the link pattern, we do not count those as
        public, because we are interested in *obviously* public fields
        clearly visible to the user.

        """

        # the display sets are not really defined at one single point…
        sets = ('contact', 'content')
        conf = configuration.display or {}

        for s in sets:
            if s not in conf:
                continue

            if fid in (as_internal_id(v) for v in conf[s]):
                return True

        # …neither is this
        txts = ('title', 'lead')

        for t in txts:
            for key in safe_format_keys(getattr(configuration, t, '')):
                if fid == as_internal_id(key):
                    return True

        # also include fields which are used as keywords
        if fid in (as_internal_id(v) for v in configuration.keywords or ()):
            return True

        # check if the field is the thumbnail
        if fid == as_internal_id(configuration.thumbnail or ''):
            return True

        return False

    @property
    def default_marker_color(self) -> str:
        return (
            (self.request.app.org.theme_options or {}).get('primary-color')
            or user_options['primary-color']
        )

    @property
    def marker_color(self) -> str | None:
        return self.marker_color_value.data

    @marker_color.setter
    def marker_color(self, value: str | None) -> None:
        self.marker_color_value.data = value or self.default_marker_color

    @property
    def configuration(self) -> DirectoryConfiguration:
        content_fields = list(self.extract_field_ids(self.content_fields))

        # Remove file and url fields from search
        file_fields = [
            f.human_id
            for f in (self.known_fields or ())
            if f.type in ('fileinput', 'multiplefileinput', 'url', 'video_url')
        ]
        searchable_content_fields = [
            f for f in content_fields if f not in file_fields
        ]
        content_hide_labels = list(
            self.extract_field_ids(self.content_hide_labels))
        contact_fields = list(self.extract_field_ids(self.contact_fields))
        keyword_fields = list(self.extract_field_ids(self.keyword_fields))
        thumbnails = list(self.extract_field_ids(self.show_as_thumbnails))

        order_format = self.data[
            self.order.data == 'by-title' and 'title_format' or 'order_format'
        ]

        assert self.title_format.data is not None
        return DirectoryConfiguration(
            title=self.title_format.data,
            lead=self.lead_format.data,
            empty_notice=self.empty_notice.data,
            order=safe_format_keys(order_format),
            keywords=keyword_fields,
            searchable=searchable_content_fields + contact_fields,
            display={
                'content': content_fields,
                'contact': contact_fields,
                'content_hide_labels': content_hide_labels
            },
            direction=self.order_direction.data,
            link_pattern=self.link_pattern.data,
            link_title=self.link_title.data,
            link_visible=self.link_visible.data,
            thumbnail=(
                self.thumbnail.data and self.thumbnail.data.splitlines()[0]
            ),
            address_block_title=(
                self.address_block_title_type.data == 'fixed'
                and self.address_block_title.data
                or None
            ),
            show_as_thumbnails=thumbnails
        )

    @configuration.setter
    def configuration(self, cfg: DirectoryConfiguration) -> None:

        def join(attr: str) -> str | None:
            return getattr(cfg, attr, None) and '\n'.join(getattr(cfg, attr))

        display = cfg.display or {}

        self.title_format.data = cfg.title
        self.lead_format.data = cfg.lead or ''
        self.empty_notice.data = cfg.empty_notice
        self.content_fields.data = '\n'.join(display.get('content', ''))
        self.content_hide_labels.data = '\n'.join(
            display.get('content_hide_labels', ''))
        self.contact_fields.data = '\n'.join(display.get('contact', ''))
        self.keyword_fields.data = join('keywords')
        self.order_direction.data = cfg.direction == 'desc' and 'desc' or 'asc'
        self.link_pattern.data = cfg.link_pattern
        self.link_title.data = cfg.link_title
        if cfg.link_visible is not None:
            self.link_visible.data = cfg.link_visible
        self.thumbnail.data = cfg.thumbnail
        self.show_as_thumbnails.data = join('show_as_thumbnails')

        if safe_format_keys(cfg.title) == cfg.order:
            self.order.data = 'by-title'
        else:
            self.order.data = 'by-format'
            self.order_format.data = ''.join(
                f'[{key}]' for key in cfg.order or ()
            )

        if cfg.address_block_title:
            self.address_block_title_type.data = 'fixed'
            self.address_block_title.data = cfg.address_block_title
        else:
            self.address_block_title_type.data = 'auto'
            self.address_block_title.data = ''

    def populate_obj(self, obj: ExtendedDirectory) -> None:  # type:ignore
        super().populate_obj(obj, exclude={
            'configuration',
            'order',
        })

        obj.configuration = self.configuration

        if self.marker_color_type.data == 'default':
            obj.marker_color = None
        else:
            obj.marker_color = self.marker_color

    def process_obj(self, obj: ExtendedDirectory) -> None:  # type:ignore
        self.configuration = obj.configuration

        if obj.marker_color:
            self.marker_color_type.data = 'custom'
            self.marker_color = obj.marker_color
        else:
            self.marker_color_type.data = 'default'
            self.marker_color = self.default_marker_color


if TYPE_CHECKING:
    # mypy doesn't understand merge_forms/move_fields, for type checking
    # the order of attributes doesn't matter so we can tell it how the
    # form should look like with basic inheritance
    class DirectoryForm(DirectoryBaseForm, PaymentForm):
        pass

else:
    class DirectoryForm(
        merge_forms(DirectoryBaseForm, PaymentForm)
    ):

        minimum_price_args = PaymentForm.minimum_price_total.kwargs.copy()
        minimum_price_args['fieldset'] = _('New entries')
        minimum_price_args['depends_on'] = ('enable_submissions', 'y')

        minimum_price_total = DecimalField(**minimum_price_args)

        payment_method_args = PaymentForm.payment_method.kwargs.copy()
        payment_method_args['fieldset'] = _('New entries')
        payment_method_args['depends_on'] = ('enable_submissions', 'y')

        payment_method = RadioField(**payment_method_args)

    DirectoryForm = move_fields(
        DirectoryForm,
        ('minimum_price_total', 'payment_method'),
        after='currency'
    )


class DirectoryImportForm(Form):

    import_config = RadioField(
        label=_('Apply directory configuration'),
        choices=(
            ('yes', _('Yes, import configuration and entries')),
            ('no', _('No, only import entries'))
        ),
        default='no',
        validators=[InputRequired()]
    )

    mode = RadioField(
        label=_('Mode'),
        choices=(
            ('new', _('Only import new entries')),
            ('replace', _('Replace all entries')),
        ),
        default='new',
        validators=[InputRequired()]
    )

    zip_file = UploadField(
        label=_('Import'),
        validators=[
            DataRequired(),
            FileSizeLimit(500 * 1024 * 1024)
        ],
        allowed_mimetypes={
            'application/zip',
            'application/octet-stream'
        },
        render_kw={'force_simple': True}
    )

    @staticmethod
    def clear_entries(session: Session, target: ExtendedDirectory) -> None:
        for existing in target.entries:
            session.delete(existing)

        target.entries.clear()
        session.flush()

    def run_import(self, target: ExtendedDirectory) -> int:
        session = object_session(target)

        count = 0

        def count_entry(entry: ExtendedDirectoryEntry) -> None:
            nonlocal count
            count += 1

        if self.mode.data == 'replace':
            self.clear_entries(session, target)

        assert self.zip_file.file is not None
        archive = DirectoryZipArchive.from_buffer(self.zip_file.file)
        archive.read(
            target=target,
            skip_existing=True,
            limit=100,
            apply_metadata=self.import_config.data == 'yes',
            after_import=count_entry
        )

        return count


class DirectoryUrlForm(ChangeAdjacencyListUrlForm):
    """For changing the URL of a directory independent of the title."""

    def validate_name(self, field: StringField) -> None:
        if not self.name.data:
            raise ValidationError(_('The name field cannot be empty.'))

        model = self.get_model()
        if model.name == self.name.data:
            raise ValidationError(_('Please fill out a new name'))

        normalized_name = normalize_for_url(self.name.data)
        if self.name.data != normalized_name:
            raise ValidationError(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )

        # Query to check if the normalized name already exists
        cls = model.__class__
        session = self.request.session
        query = session.query(cls).filter(
            cls.name == normalized_name
        )
        if session.query(query.exists()).scalar():
            raise ValidationError(
                _('An entry with the same name exists')
            )


class DirectoryRecipientForm(Form):
    """Form for adding recipients of entry updates to the directory."""

    address = EmailField(
        label=_('E-Mail'),
        description='peter.muster@example.org',
        validators=[InputRequired(), Email()]
    )
