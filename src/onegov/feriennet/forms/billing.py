from __future__ import annotations

from functools import cached_property
from onegov.activity import BookingPeriodInvoice
from onegov.feriennet import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.user import User, UserCollection
from sqlalchemy import func
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from sqlalchemy.orm import Query


class BillingForm(Form):

    confirm = RadioField(
        label=_('Confirm billing:'),
        default='no',
        choices=[
            ('no', _('No, preview only')),
            ('yes', _('Yes, confirm billing'))
        ]
    )

    sure = BooleanField(
        label=_(
            'I know that after confirmation, bills are made visible to users.'
        ),
        default=False,
        depends_on=('confirm', 'yes')
    )

    @property
    def finalize_period(self) -> bool:
        return self.confirm.data == 'yes' and self.sure.data is True


class ManualBookingForm(Form):

    target = RadioField(
        label=_('Target'),
        choices=()
    )

    tags = MultiCheckboxField(
        label=_('Tags'),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-users-with-tags'),
        choices=()
    )

    username = SelectField(
        label=_('User'),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-user'),
    )

    booking_text = StringField(
        label=_('Booking Text'),
        validators=(InputRequired(), )
    )

    kind = RadioField(
        label=_('Kind'),
        default='discount',
        choices=(
            ('discount', _('Discount')),
            ('surcharge', _('Surcharge'))
        )
    )

    discount = DecimalField(
        label=_('Discount'),
        validators=(InputRequired(), ),
        depends_on=('kind', 'discount')
    )

    surcharge = DecimalField(
        label=_('Surcharge'),
        validators=(InputRequired(), ),
        depends_on=('kind', 'surcharge')
    )

    @property
    def amount(self) -> Decimal:
        if self.kind.data == 'discount':
            assert self.discount.data is not None
            return -self.discount.data
        elif self.kind.data == 'surcharge':
            assert self.surcharge.data is not None
            return self.surcharge.data
        else:
            raise NotImplementedError

    @property
    def text(self) -> str | None:
        return self.booking_text.data

    @property
    def available_usernames(self) -> Query[tuple[str, str]]:
        return (
            self.usercollection.query()  # type: ignore[return-value]
            .with_entities(User.username, User.realname)
            .filter(func.trim(func.coalesce(User.realname, '')) != '')
            .filter(User.active == True)
            .order_by(func.unaccent(func.lower(User.realname)))
            .tuples()
        )

    @property
    def users(self) -> tuple[str, ...]:
        if self.target.data == 'all':
            return tuple(username for username, _ in self.available_usernames)

        elif self.target.data == 'for-user':
            return (self.username.data, )

        elif self.target.data == 'for-users-with-tags':
            assert self.tags.data is not None
            return self.usercollection.usernames_by_tags(self.tags.data)

        else:
            raise NotImplementedError

    def on_request(self) -> None:
        self.target.choices = [
            ('all', _('All')),
            ('for-user', _('For a specific user'))
        ]

        self.load_usernames()
        self.load_user_tags()

        if self.tags.choices:
            self.target.choices.append(
                ('for-users-with-tags', _('For users with tags')))

        if (self.request.params.get('for-user')
                and not self.target.data):
            self.target.data = 'for-user'
            if not self.username.data:
                self.username.data = self.request.params['for-user']

    @property
    def usercollection(self) -> UserCollection:
        return UserCollection(self.request.session)

    def load_user_tags(self) -> None:
        self.tags.choices = [(t, t) for t in self.usercollection.tags]

    def load_usernames(self) -> None:
        self.username.choices = list(self.available_usernames)


class PaymentWithDateForm(Form):

    payment_date = DateField(
        label=_('Payment date'),
        validators=(InputRequired(), ),
    )

    target = RadioField(
        validators=(InputRequired(), ),
        label=_('Target'),
        choices=(
            ('all', _('Whole invoice')),
            ('specific', _('Only for specific items'))
        ),
    )

    items = MultiCheckboxField(
        label=_('Items'),
        validators=(InputRequired(), ),
        depends_on=('target', 'specific'),
        choices=()
    )

    def on_request(self) -> None:
        self.items.choices = [
            (i.id.hex,
             f'{i.group} - {i.text} ({round(i.amount, 2)})')
            for i in self.invoice.items if not i.paid]

        if self.request.params['item-id'] != 'all':
            # Set defaults according to parameters
            if not self.target.data:
                self.target.data = 'specific'
            if not self.items.data:
                self.items.data = [self.request.params['item-id']]

            # Check all unpaid items if 'all' is selected
            if self.target.data == 'all':
                self.items.data = [i.id.hex for i in self.invoice.items
                                   if not i.paid]
        else:
            # Set defaults according to parameters
            if not self.target.data:
                self.target.data = 'all'
            if not self.items.data:
                self.items.data = [i.id.hex for i in self.invoice.items
                                   if not i.paid]

            # Check all unpaid items if 'all' is selected
            if self.target.data == 'all':
                self.items.data = [i.id.hex for i in self.invoice.items]

    @cached_property
    def invoice(self) -> BookingPeriodInvoice:
        return self.request.session.query(
            BookingPeriodInvoice).filter_by(id=self.request.params['invoice-id']).one()
