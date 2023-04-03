from onegov.activity import Invoice
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


class BillingForm(Form):

    confirm = RadioField(
        label=_("Confirm billing:"),
        default='no',
        choices=[
            ('no', _("No, preview only")),
            ('yes', _("Yes, confirm billing"))
        ]
    )

    sure = BooleanField(
        label=_(
            "I know that after confirmation, bills are made visible to users."
        ),
        default=False,
        depends_on=('confirm', 'yes')
    )

    @property
    def finalize_period(self):
        return self.confirm.data == 'yes' and self.sure.data is True


class ManualBookingForm(Form):

    target = RadioField(
        label=_("Target"),
        choices=tuple()
    )

    tags = MultiCheckboxField(
        label=_("Tags"),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-users-with-tags'),
        choices=tuple()
    )

    username = SelectField(
        label=_("User"),
        validators=(InputRequired(), ),
        depends_on=('target', 'for-user'),
    )

    booking_text = StringField(
        label=_("Booking Text"),
        validators=(InputRequired(), )
    )

    kind = RadioField(
        label=_("Kind"),
        default='discount',
        choices=(
            ('discount', _("Discount")),
            ('surcharge', _("Surcharge"))
        )
    )

    discount = DecimalField(
        label=_("Discount"),
        validators=(InputRequired(), ),
        depends_on=('kind', 'discount')
    )

    surcharge = DecimalField(
        label=_("Surcharge"),
        validators=(InputRequired(), ),
        depends_on=('kind', 'surcharge')
    )

    @property
    def amount(self):
        if self.kind.data == 'discount':
            return -self.discount.data
        elif self.kind.data == 'surcharge':
            return self.surcharge.data
        else:
            raise NotImplementedError

    @property
    def text(self):
        return self.booking_text.data

    @property
    def available_usernames(self):
        return self.usercollection.query()\
            .with_entities(User.username, User.realname)\
            .filter(func.trim(func.coalesce(User.realname, "")) != "")\
            .filter(User.active == True)\
            .order_by(func.unaccent(func.lower(User.realname)))

    @property
    def users(self):
        if self.target.data == 'all':
            return tuple(u.username for u in self.available_usernames)

        elif self.target.data == 'for-user':
            return (self.username.data, )

        elif self.target.data == 'for-users-with-tags':
            return self.usercollection.usernames_by_tags(self.tags.data)

        else:
            raise NotImplementedError

    def on_request(self):
        self.target.choices = [
            ('all', _("All")),
            ('for-user', _("For a specific user"))
        ]

        self.load_usernames()
        self.load_user_tags()

        if self.tags.choices:
            self.target.choices.append(
                ('for-users-with-tags', _("For users with tags")))

        if self.request.params.get('for-user'):
            self.target.data = 'for-user'
            self.username.data = self.request.params['for-user']

    @property
    def usercollection(self):
        return UserCollection(self.request.session)

    def load_user_tags(self):
        self.tags.choices = tuple(
            (t, t) for t in self.usercollection.tags)

    def load_usernames(self):
        self.username.choices = tuple(
            (u.username, u.realname) for u in self.available_usernames
        )


class PaymentWithDateForm(Form):

    payment_date = DateField(
        label=_("Payment date"),
        validators=(InputRequired(), ),
    )

    target = RadioField(
        validators=(InputRequired(), ),
        label=_("Target"),
        choices=(
            ('all', _("Whole invoice")),
            ('specific', _("Only for specific items"))
        ),
        default='all',
    )

    items = MultiCheckboxField(
        label=_("Items"),
        validators=(InputRequired(), ),
        depends_on=('target', 'specific'),
        choices=tuple()
    )

    def on_request(self):
        self.items.choices = [
            (i.id.hex,
             f'{i.group} - {i.text} ({round(i.amount, 2)})')
            for i in self.invoice.items if not i.paid]

        if self.request.params['item-id'] != 'all':
            self.target.data = 'specific'
            self.items.data = [self.request.params['item-id']]
        else:
            self.items.data = [i.id.hex for i in self.invoice.items
                               if not i.paid]

    @property
    def invoice(self):
        return self.request.session.query(
            Invoice).filter_by(id=self.request.params['invoice-id']).first()
