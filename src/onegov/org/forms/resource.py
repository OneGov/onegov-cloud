from wtforms.fields import BooleanField
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import ValidationError

from onegov.form import Form, merge_forms, parse_formcode
from onegov.form.fields import MultiCheckboxField
from onegov.form.filters import as_float
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import DateRangeForm
from onegov.org.forms.generic import ExportForm
from onegov.org.forms.generic import PaymentForm
from onegov.org.forms.reservation import (
    RESERVED_FIELDS, ExportToExcelWorksheets)
from onegov.org.forms.util import WEEKDAYS


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.reservation import Resource


class ResourceBaseForm(Form):
    """ Defines the form for all resources. """

    title = StringField(_('Title'), [InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this reservation resource is about'),
        render_kw={'rows': 4})

    group = StringField(
        label=_('Group'),
        description=_('Used to group the resource in the overview')
    )

    text = HtmlField(
        label=_('Text'))

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
        default='agendaWeek',
        validators=[InputRequired()],
        choices=(
            ('agendaWeek', _('Week view')),
            ('month', _('Month view')),
        ))

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

    def on_request(self) -> None:
        if hasattr(self.model, 'type'):
            if self.model.type == 'daypass':
                self.delete_field('default_view')
        else:
            if self.request.view_name.endswith('new-daypass'):
                self.delete_field('default_view')

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

    def populate_obj(self, obj: 'Resource') -> None:  # type:ignore
        super().populate_obj(obj, exclude=('deadline', 'zipcode_block'))
        obj.deadline = self.deadline
        obj.zipcode_block = self.zipcode_block

    def process_obj(self, obj: 'Resource') -> None:  # type:ignore
        super().process_obj(obj)
        self.deadline = obj.deadline
        self.zipcode_block = obj.zipcode_block


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
