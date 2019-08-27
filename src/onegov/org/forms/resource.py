from onegov.form import Form, merge_forms
from onegov.form.validators import ValidFormDefinition
from onegov.form.filters import as_float
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import DateRangeForm
from onegov.org.forms.generic import ExportForm
from onegov.org.forms.generic import PaymentMethodForm
from onegov.org.forms.reservation import RESERVED_FIELDS
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import TextField
from wtforms import validators
from wtforms.fields.html5 import DecimalField, IntegerField


class ResourceBaseForm(Form):
    """ Defines the form for all resources. """
    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this reservation resource is about"),
        render_kw={'rows': 4})

    group = StringField(
        label=_("Group"),
        description=_("Used to group the resource in the overview")
    )

    text = HtmlField(
        label=_("Text"))

    definition = TextAreaField(
        label=_("Extra Fields Definition"),
        validators=[
            validators.Optional(),
            ValidFormDefinition(
                require_email_field=False,
                reserved_fields=RESERVED_FIELDS
            )
        ],
        render_kw={'rows': 32, 'data-editor': 'form'}
    )

    deadline_unit = RadioField(
        label=_("Closing date for the public"),
        fieldset=_("Closing date"),
        default='n',
        validators=[validators.InputRequired()],
        choices=(
            ('n', _(
                "No closing date")),
            ('d', _(
                "Stop accepting reservations days before the allocation")),
            ('h', _(
                "Stop accepting reservations hours before the allocation")),
        )
    )

    deadline_hours = IntegerField(
        label=_("Hours"),
        fieldset=_("Closing date"),
        depends_on=('deadline_unit', 'h'),
        default=1,
        validators=[
            validators.InputRequired(),
            validators.NumberRange(min=1)
        ]
    )

    deadline_days = IntegerField(
        label=_("Days"),
        fieldset=_("Closing date"),
        depends_on=('deadline_unit', 'd'),
        default=1,
        validators=[
            validators.InputRequired(),
            validators.NumberRange(min=1)
        ]
    )

    pricing_method = RadioField(
        label=_("Price"),
        fieldset=_("Payments"),
        default='free',
        validators=[validators.InputRequired()],
        choices=(
            ('free', _("Free of charge")),
            ('per_item', _("Per item")),
            ('per_hour', _("Per hour"))
        )
    )

    price_per_item = DecimalField(
        label=_("Price per item"),
        filters=(as_float, ),
        fieldset=_("Payments"),
        validators=[validators.Optional()],
        depends_on=('pricing_method', 'per_item')
    )

    price_per_hour = DecimalField(
        label=_("Price per hour"),
        filters=(as_float, ),
        fieldset=_("Payments"),
        validators=[validators.Optional()],
        depends_on=('pricing_method', 'per_hour')
    )

    currency = TextField(
        label=_("Currency"),
        default="CHF",
        fieldset=_("Payments"),
        depends_on=('pricing_method', '!free'),
        validators=[validators.InputRequired()],
    )

    def ensure_valid_price(self):
        if self.pricing_method.data == 'per_item':
            if not float(self.price_per_item.data) > 0:
                self.price_per_item.errors.append(_(
                    "The price must be larger than zero"
                ))
                return False

        if self.pricing_method.data == 'per_hour':
            if not float(self.price_per_hour.data) > 0:
                self.price_per_hour.errors.append(_(
                    "The price must be larger than zero"
                ))
                return False

    @property
    def deadline(self):
        if self.deadline_unit.data == 'h':
            return (self.deadline_hours.data, 'h')

        if self.deadline_unit.data == 'd':
            return (self.deadline_days.data, 'd')

        return None

    @deadline.setter
    def deadline(self, value):
        self.deadline_unit.data = 'n'

        if not value:
            return

        value, unit = value
        self.deadline_unit.data = unit

        if unit == 'h':
            self.deadline_hours.data = value
        elif unit == 'd':
            self.deadline_days.data = value
        else:
            raise NotImplementedError()

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude=('deadline', ))
        obj.deadline = self.deadline

    def process_obj(self, obj):
        super().process_obj(obj)
        self.deadline = obj.deadline


class ResourceForm(merge_forms(ResourceBaseForm, PaymentMethodForm)):
    pass


class ResourceCleanupForm(DateRangeForm):
    """ Defines the form to remove multiple allocations. """


class ResourceExportForm(merge_forms(DateRangeForm, ExportForm)):
    """ Resource export form with start/end date. """
