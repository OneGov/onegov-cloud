from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.form.core import Form
from onegov.form.fields import ChosenSelectMultipleField, TranslatedSelectField
from onegov.org import _
from onegov.ticket import handlers as ticket_handlers
from operator import itemgetter
from wtforms import DateField, RadioField
from wtforms.validators import Optional


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.pay import PaymentCollection
    from onegov.ticket import TicketCollection, TicketInvoiceCollection
    from wtforms.fields.choices import _Choice


def coerce_optional_bool(choice: str | bool | None) -> bool | None:
    if isinstance(choice, str):
        match choice.lower():
            case 'true':
                return True
            case 'false':
                return False
            case _:
                return None
    return choice


def get_ticket_group_choices(request: CoreRequest) -> list[_Choice]:
    tickets: TicketCollection | None
    # NOTE: This is a little bit expensive, but since we don't use the
    #       same ticket collection class in every application this is
    #       easier than overwriting these forms in every application
    tickets = request.resolve_path('/tickets/ALL/all')
    if tickets is None:
        return []

    handlers: list[tuple[str, str]] = []

    groups = dict(tickets.groups_by_handler_code())
    for handler_code in groups:
        if handler_code not in ticket_handlers.registry:
            continue
        handler = ticket_handlers.get(handler_code)
        assert hasattr(handler, 'handler_title')
        handlers.append(
            (handler_code, request.translate(handler.handler_title))
        )

    handlers.sort(key=itemgetter(1))

    choices: list[_Choice] = []

    for handler_code, title in handlers:
        handler_groups = groups[handler_code]
        handler_groups.sort(key=normalize_for_url)

        choices.append((
            handler_code,
            title,
            {
                'class': f'{handler_code}-link'
                f'{" is-parent" if handler_groups else ""}'
            }
        ))
        choices.extend(
            (
                f'{handler_code}-{group}',
                group,
                {'class': f'{handler_code}-sub-link ticket-group-filter'}
            )
            for group in handler_groups
        )

    return choices


class TicketInvoiceSearchForm(Form):

    css_class = 'resettable'

    invoiced = TranslatedSelectField(
        label=_('Status'),
        fieldset=_('Filter Invoices'),
        choices=[
            ('None', _('All')),
            ('False', _('Uninvoiced')),
            ('True', _('Invoiced')),
        ],
        coerce=coerce_optional_bool,
        default=None,
    )

    has_payment = TranslatedSelectField(
        label=_('Net Amount'),
        fieldset=_('Filter Invoices'),
        choices=[
            ('None', _('All')),
            ('True', '> 0.00'),
            ('False', '≤ 0.00'),
        ],
        coerce=coerce_optional_bool,
        default=None,
    )

    ticket_group = ChosenSelectMultipleField(
        label=_('Ticket category'),
        fieldset=_('Filter Invoices'),
        choices=[],
    )

    ticket_start_date = DateField(
        label=_('Ticket created from date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
        validators=[Optional()]
    )

    ticket_end_date = DateField(
        label=_('Ticket created to date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
        validators=[Optional()]
    )

    reservation_start_date = DateField(
        label=_('From reservation date'),
        fieldset=_('Filter by Reservation Date'),
        validators=[Optional()]
    )

    reservation_end_date = DateField(
        label=_('To reservation date'),
        fieldset=_('Filter by Reservation Date'),
        validators=[Optional()]
    )

    reservation_reference_date = RadioField(
        label=_('Reference date'),
        choices=(
            ('final', _('Final reservation date')),
            ('any', _('Any reservation date')),
        ),
        fieldset=_('Filter by Reservation Date'),
        default='final',
    )

    def on_request(self) -> None:
        self.ticket_group.choices = get_ticket_group_choices(self.request)

    def apply_model(self, model: TicketInvoiceCollection) -> None:
        """Populate the form fields from the model's filter values."""
        self.has_payment.data = model.has_payment
        self.invoiced.data = model.invoiced
        self.ticket_group.data = model.ticket_group or []
        self.ticket_start_date.data = model.ticket_start
        self.ticket_end_date.data = model.ticket_end
        self.reservation_start_date.data = model.reservation_start
        self.reservation_end_date.data = model.reservation_end
        self.reservation_reference_date.data = model.reservation_reference_date

    def update_model(self, model: TicketInvoiceCollection) -> None:
        """Update the model's filter values from the form's data."""
        model.has_payment = self.has_payment.data
        model.invoiced = self.invoiced.data
        model.ticket_group = self.ticket_group.data or []
        model.ticket_start = self.ticket_start_date.data
        model.ticket_end = self.ticket_end_date.data
        model.reservation_start = self.reservation_start_date.data
        model.reservation_end = self.reservation_end_date.data
        model.reservation_reference_date = self.reservation_reference_date.data
        # Reset to the first page when filters change
        model.page = 0


class PaymentSearchForm(Form):

    css_class = 'resettable'

    status = TranslatedSelectField(
        label=_('Status'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('open', _('Open')),
            ('paid', _('Paid')),
            ('invoiced', _('Invoiced'))
        ],
        default='',
    )

    payment_type = TranslatedSelectField(
        label=_('Payment Type'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('manual', _('Manual')),
            ('provider', _('Payment Provider'))
        ],
        default='',
    )

    ticket_group = ChosenSelectMultipleField(
        label=_('Ticket category'),
        fieldset=_('Filter Payments'),
        choices=[],
    )

    ticket_start_date = DateField(
        label=_('Ticket created from date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
        validators=[Optional()]
    )

    ticket_end_date = DateField(
        label=_('Ticket created to date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
        validators=[Optional()]
    )

    reservation_start_date = DateField(
        label=_('From reservation date'),
        fieldset=_('Filter by Reservation Date'),
        validators=[Optional()]
    )

    reservation_end_date = DateField(
        label=_('To reservation date'),
        fieldset=_('Filter by Reservation Date'),
        validators=[Optional()]
    )

    reservation_reference_date = RadioField(
        label=_('Reference date'),
        choices=(
            ('final', _('Final reservation date')),
            ('any', _('Any reservation date')),
        ),
        fieldset=_('Filter by Reservation Date'),
        default='final',
        validators=[Optional()]
    )

    def apply_model(self, model: PaymentCollection) -> None:
        """Populate the form fields from the model's filter values."""
        self.reservation_start_date.data = model.reservation_start
        self.reservation_end_date.data = model.reservation_end
        self.reservation_reference_date.data = model.reservation_reference_date
        self.status.data = model.status or ''
        self.ticket_group.data = model.ticket_group or []
        self.ticket_start_date.data = model.ticket_start
        self.ticket_end_date.data = model.ticket_end
        self.payment_type.data = model.payment_type or ''

    def update_model(self, model: PaymentCollection) -> None:
        """Update the model's filter values from the form's data."""
        model.reservation_start = self.reservation_start_date.data
        model.reservation_end = self.reservation_end_date.data
        model.reservation_reference_date = self.reservation_reference_date.data
        model.status = self.status.data or None
        model.ticket_group = self.ticket_group.data or []
        model.ticket_start = self.ticket_start_date.data
        model.ticket_end = self.ticket_end_date.data
        model.payment_type = self.payment_type.data or None
        # Reset to the first page when filters change
        model.page = 0

    def on_request(self) -> None:
        self.ticket_group.choices = get_ticket_group_choices(self.request)
