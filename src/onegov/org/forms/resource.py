from __future__ import annotations

from functools import cached_property
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import merge_forms
from onegov.form import parse_formcode
from onegov.form import Form
from onegov.form.errors import FormError
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.filters import as_float
from onegov.form.validators import ValidFormDefinition
from onegov.form.widgets import ChosenSelectWidget
from onegov.org import _, log
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import DateRangeForm
from onegov.org.forms.generic import ExportForm
from onegov.org.forms.generic import PaymentForm
from onegov.org.forms.reservation import (
    RESERVED_FIELDS, ExportToExcelWorksheets)
from onegov.org.forms.util import WEEKDAYS
from onegov.org.kaba import KabaApiError, KabaClient
from wtforms.fields import BooleanField
from wtforms.fields import DecimalField
from wtforms.fields import EmailField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup
    from onegov.org.request import OrgRequest
    from onegov.reservation import Resource
    from wtforms import Field


def coerce_component_tuple(value: Any) -> tuple[str, str] | None:
    if not value:
        return None

    if isinstance(value, str):
        value = value.rsplit(':', 1)

    site_id, component = value
    return site_id, component


class ComponentSelectWidget(ChosenSelectWidget):
    @classmethod
    def render_option(
        cls,
        value: Any,
        label: str,
        selected: bool,
        **kwargs: Any
    ) -> Markup:
        if value:
            value = ':'.join(value)
        else:
            value = ''
        return super().render_option(value, label, selected, **kwargs)


class ResourceBaseForm(Form):
    """ Defines the form for all resources. """

    if TYPE_CHECKING:
        request: OrgRequest

    title = StringField(_('Title'), [InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this reservation resource is about'),
        render_kw={'rows': 4})

    group = StringField(
        label=_('Group'),
        description=_('Used to group the resource in the overview')
    )

    subgroup = StringField(
        label=_('Subgroup'),
        description=_('Used to group the resource in the overview')
    )

    text = HtmlField(
        label=_('Text')
    )

    confirmation_text = HtmlField(
        label=_('Additional information for confirmed reservations'),
        description=_('This text will be included in the confirmation '
                      'and reservation summary e-mails sent out to '
                      'customers. As well as displayed on the ticket '
                      'status page, once reservations have been accepted.')
    )

    pick_up = TextAreaField(
        label=_('Pick-Up'),
        description=_('Describes how this resource can be picked up. '
                      'This text is used on the ticket status page to '
                      'inform the user')
    )

    definition = TextAreaField(
        label=_('Extra Fields Definition'),
        validators=[
            Optional(),
            ValidFormDefinition(
                require_email_field=False,
                reserved_fields=RESERVED_FIELDS
            )
        ],
        render_kw={'rows': 32, 'data-editor': 'form'}
    )

    ical_fields = TextAreaField(
        label=_('Extra Field values to include in calendar subscription'),
        description=_(
            'By default only the e-mail address and link to the ticket '
            'is included. You may wish to include additional administrative '
            'information like a phone number, name or address. Please be '
            'aware however that this data can be viewed by anyone that '
            'knows the subscription URL, so only include what you must.'
        ),
        fieldset=_('Calendar Subscription'),
        render_kw={'class_': 'formcode-select'}
    )

    deadline_unit = RadioField(
        label=_('Closing date for the public'),
        fieldset=_('Closing date'),
        default='n',
        validators=[InputRequired()],
        choices=(
            ('n', _(
                'No closing date')),
            ('d', _(
                'Stop accepting reservations days before the allocation')),
            ('h', _(
                'Stop accepting reservations hours before the allocation')),
        )
    )

    deadline_hours = IntegerField(
        label=_('Hours'),
        fieldset=_('Closing date'),
        depends_on=('deadline_unit', 'h'),
        default=1,
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    deadline_days = IntegerField(
        label=_('Days'),
        fieldset=_('Closing date'),
        depends_on=('deadline_unit', 'd'),
        default=1,
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    lead_time_unit = RadioField(
        label=_('Opening date for the public'),
        fieldset=_('Opening date'),
        default='n',
        validators=[InputRequired()],
        choices=(
            ('n', _(
                'No opening date')),
            ('d', _(
                'Start accepting reservations days before the allocation')),
        )
    )

    lead_time_days = IntegerField(
        label=_('Days'),
        fieldset=_('Opening date'),
        depends_on=('lead_time_unit', 'd'),
        default=1,
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    zipcode_block_use = BooleanField(
        label=_('Limit reservations to certain zip-codes'),
        fieldset=_('Zip-code limit'),
        default=False,
    )

    zipcode_field = TextAreaField(
        label=_('Zip-code field'),
        fieldset=_('Zip-code limit'),
        depends_on=('zipcode_block_use', 'y'),
        validators=[InputRequired()],
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'text',
            'data-type': 'radio',
        })

    zipcode_list = TextAreaField(
        label=_('Allowed zip-codes (one per line)'),
        fieldset=_('Zip-code limit'),
        depends_on=('zipcode_block_use', 'y'),
        validators=[InputRequired()],
        render_kw={
            'rows': 4
        }
    )

    zipcode_days = IntegerField(
        label=_('Days before an allocation may be reserved by anyone'),
        fieldset=_('Zip-code limit'),
        depends_on=('zipcode_block_use', 'y'),
        validators=[
            InputRequired(),
            NumberRange(min=0)
        ],
    )

    # only used for rooms, not day-passes
    default_view = RadioField(
        label=_('Default view'),
        fieldset=_('View'),
        default='timeGridWeek',
        validators=[InputRequired()],
        choices=(
            ('timeGridWeek', _('Week view')),
            ('dayGridMonth', _('Month view')),
        ))

    kaba_components = ChosenSelectMultipleField(
        label=_('Doors'),
        choices=(),
        coerce=coerce_component_tuple,
        fieldset='dormakaba',
        widget=ComponentSelectWidget(multiple=True)
    )

    reply_to = EmailField(
        label=_('E-Mail Reply Address (Reply-To)'),
        fieldset=_('Tickets'),
        description=_('Replies to automated e-mails go to this address.')
    )

    invoicing_party = TextAreaField(
        label=_('Invoicing party'),
        fieldset=_('Invoicing'),
        description=_('Will be displayed in invoices'),
        render_kw={'rows': 3}
    )

    cost_object = StringField(
        label=_('Cost center / cost unit'),
        fieldset=_('Invoicing'),
        description=_(
            'Will be displayed in invoices for any costs directly '
            'associated with reservations on this resource.'
        )
    )

    pricing_method = RadioField(
        label=_('Price'),
        fieldset=_('Payments'),
        default='free',
        validators=[InputRequired()],
        choices=(
            ('free', _('Free of charge')),
            ('per_item', _('Per item')),
            ('per_hour', _('Per hour'))
        )
    )

    price_per_item = DecimalField(
        label=_('Price per item'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_item')
    )

    price_per_hour = DecimalField(
        label=_('Price per hour'),
        filters=(as_float,),
        fieldset=_('Payments'),
        validators=[InputRequired()],
        depends_on=('pricing_method', 'per_hour')
    )

    currency = StringField(
        label=_('Currency'),
        default='CHF',
        fieldset=_('Payments'),
        depends_on=('pricing_method', '!free'),
        validators=[InputRequired()],
    )

    extras_pricing_method = RadioField(
        label=_('Prices in extra fields are'),
        description=_(
            'If no extra fields are defined or none of the extra fields '
            'contain pricing information, then this setting has no effect.'
        ),
        fieldset=_('Payments'),
        default='per_item',
        validators=[InputRequired()],
        choices=(
            ('one_off', _('One-off')),
            ('per_item', _('Per item')),
            ('per_hour', _('Per hour'))
        )
    )

    def on_request(self) -> None:
        if hasattr(self.model, 'type'):
            if self.model.type == 'daypass':
                self.delete_field('default_view')
                self.delete_field('kaba_components')
                return
        else:
            if self.request.view_name.endswith('new-daypass'):
                self.delete_field('default_view')
                self.delete_field('kaba_components')
                return

        clients = KabaClient.from_app(self.request.app)
        if not clients:
            self.delete_field('kaba_components')
            return

        try:
            self.kaba_components.choices = [
                choice
                for client in clients.values()
                for choice in client.component_choices()
            ]
        except KabaApiError:
            log.info('Kaba API error', exc_info=True)
            self.request.alert(_(
                'Failed to retrieve the doors from the dormakaba API '
                'please make sure your credentials are still valid.'
            ))
            self.delete_field('kaba_components')

    @cached_property
    def known_field_ids(self) -> set[str] | None:
        # FIXME: We should probably define this in relation to known_fields
        #        so we don't parse the form twice if we access both properties
        try:
            return {
                field.id for field in
                flatten_fieldsets(parse_formcode(self.definition.data))
            }
        except FormError:
            return None

    def extract_field_ids(self, field: Field) -> list[str]:
        if not self.known_field_ids:
            return []

        return [
            name
            for line in field.data.splitlines()
            if as_internal_id(name := line.strip()) in self.known_field_ids
        ]

    @property
    def zipcodes(self) -> list[int]:
        assert self.zipcode_list.data is not None
        return [int(z) for z in self.zipcode_list.data.split()]

    def validate_zipcode_field(self, field: TextAreaField) -> None:
        if not self.zipcode_block_use.data:
            return

        if not self.zipcode_field.data:
            raise ValidationError(
                _('Please select the form field that holds the zip-code'))

        for fieldset in parse_formcode(self.definition.data):
            for parsed_field in fieldset.fields:
                if parsed_field.human_id == self.zipcode_field.data:
                    return

        raise ValidationError(
            _('Please select the form field that holds the zip-code'))

    def validate_zipcode_list(self, field: TextAreaField) -> None:
        if not self.zipcode_block_use.data:
            return

        if not self.zipcode_list.data:
            raise ValidationError(
                _('Please enter at least one zip-code'))

        try:
            self.zipcodes  # noqa: B018
        except ValueError as exception:
            raise ValidationError(
                _(
                    'Please enter one zip-code per line, '
                    'without spaces or commas'
                )
            ) from exception

    def ensure_valid_price(self) -> bool | None:
        if self.pricing_method.data == 'per_item':
            if not float(self.price_per_item.data or 0) > 0:
                assert isinstance(self.price_per_item.errors, list)
                self.price_per_item.errors.append(_(
                    'The price must be larger than zero'
                ))
                return False

        if self.pricing_method.data == 'per_hour':
            if not float(self.price_per_hour.data or 0) > 0:
                assert isinstance(self.price_per_hour.errors, list)
                self.price_per_hour.errors.append(_(
                    'The price must be larger than zero'
                ))
                return False
        return None

    @property
    def deadline(self) -> tuple[int, Literal['d', 'h']] | None:
        if self.deadline_unit.data == 'h':
            assert self.deadline_hours.data is not None
            return (self.deadline_hours.data, 'h')

        if self.deadline_unit.data == 'd':
            assert self.deadline_days.data is not None
            return (self.deadline_days.data, 'd')

        return None

    @deadline.setter
    def deadline(self, value: tuple[int, Literal['d', 'h']] | None) -> None:
        self.deadline_unit.data = 'n'

        if not value:
            return

        amount, unit = value
        self.deadline_unit.data = unit

        if unit == 'h':
            self.deadline_hours.data = amount
        elif unit == 'd':
            self.deadline_days.data = amount
        else:
            raise NotImplementedError()

    @property
    def lead_time(self) -> int | None:
        if self.lead_time_unit.data == 'd':
            return self.lead_time_days.data
        return None

    @lead_time.setter
    def lead_time(self, value: int | None) -> None:
        self.lead_time_unit.data = 'd' if value else 'n'
        self.lead_time_days.data = value

    # FIXME: Use TypedDict?
    @property
    def zipcode_block(self) -> dict[str, Any] | None:
        if not self.zipcode_block_use.data:
            return None

        assert self.zipcode_days.data is not None
        return {
            'zipcode_field': self.zipcode_field.data,
            'zipcode_list': self.zipcodes,
            'zipcode_days': int(self.zipcode_days.data),
        }

    @zipcode_block.setter
    def zipcode_block(self, value: dict[str, Any] | None) -> None:
        if not value:
            self.zipcode_block_use.data = False
            return

        self.zipcode_block_use.data = True
        self.zipcode_field.data = value['zipcode_field']
        self.zipcode_days.data = value['zipcode_days']
        self.zipcode_list.data = '\n'.join(
            str(i) for i in sorted(value['zipcode_list']))

    def populate_obj(self, obj: Resource) -> None:  # type:ignore
        super().populate_obj(obj, exclude={
            'deadline',
            'deadline_unit',
            'deadline_days',
            'deadline_hours',
            'ical_fields',
            'lead_time',
            'lead_time_unit',
            'lead_time_days',
            'zipcode_block',
            'zipcode_block_use',
            'zipcode_field',
            'zipcode_days',
            'zipcode_list',
        })
        obj.deadline = self.deadline
        obj.lead_time = self.lead_time
        obj.zipcode_block = self.zipcode_block
        obj.ical_fields = list(self.extract_field_ids(self.ical_fields))

    def process_obj(self, obj: Resource) -> None:  # type:ignore
        super().process_obj(obj)
        self.deadline = obj.deadline
        self.lead_time = obj.lead_time
        self.zipcode_block = obj.zipcode_block
        self.ical_fields.data = '\n'.join(obj.ical_fields)


if TYPE_CHECKING:
    class ResourceForm(ResourceBaseForm, PaymentForm):
        pass
else:
    class ResourceForm(
        merge_forms(ResourceBaseForm, PaymentForm)
    ):
        pass


class ResourceCleanupForm(DateRangeForm):
    """ Defines the form to remove multiple allocations. """

    weekdays = MultiCheckboxField(
        label=_('Weekdays'),
        choices=WEEKDAYS,
        coerce=int,
        validators=[InputRequired()],
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        })


if TYPE_CHECKING:
    class ResourceExportForm(DateRangeForm, ExportForm):
        pass

    class AllResourcesExportForm(DateRangeForm, ExportToExcelWorksheets):
        pass
else:
    class ResourceExportForm(
        merge_forms(DateRangeForm, ExportForm)
    ):
        """ Resource export form with start/end date. """

    class AllResourcesExportForm(
        merge_forms(DateRangeForm, ExportToExcelWorksheets)
    ):
        """ Resource export all resources, with start/end date. """
