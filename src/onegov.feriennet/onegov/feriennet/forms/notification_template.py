from onegov.activity import Activity
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period
from onegov.feriennet import _
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.collections import BillingCollection
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.user import User, UserCollection
from sqlalchemy import distinct, or_, func, and_
from wtforms.fields import StringField, TextAreaField, RadioField
from wtforms.validators import InputRequired
from uuid import uuid4


class NotificationTemplateForm(Form):

    subject = StringField(
        label=_("Subject"),
        validators=[InputRequired()]
    )

    text = TextAreaField(
        label=_("Message"),
        validators=[InputRequired()],
        render_kw={'rows': 12}
    )


class NotificationTemplateSendForm(Form):

    send_to = RadioField(
        label=_("Send to (applies to active period only)"),
        choices=[
            ('myself', _(
                "Myself"
            )),
            ('active_organisers', _(
                "Organisers with an occasion"
            )),
            ('by_role', _(
                "Users of a given role"
            )),
            ('with_wishlist', _(
                "Users with wishes"
            )),
            ('with_bookings', _(
                "Users with bookings"
            )),
            ('with_unpaid_bills', _(
                "Users with unpaid bills"
            )),
            ('by_occasion', _(
                "Users with attendees of a given occasion"
            )),
        ],
        default='by_role'
    )

    roles = MultiCheckboxField(
        label=_("Role"),
        choices=[
            ('admin', _("Administrators")),
            ('editor', _("Organisers")),
            ('member', _("Members"))
        ],
        depends_on=('send_to', 'by_role')
    )

    occasion = MultiCheckboxField(
        label=_("Occasion"),
        choices=None,
        depends_on=('send_to', 'by_occasion')
    )

    state = MultiCheckboxField(
        label=_("Useraccounts"),
        choices=[
            ('active', _("Active users")),
            ('inactive', _("Inactive users")),
        ],
        default=['active'],
    )

    def on_request(self):
        self.populate_occasion()

    @property
    def has_choices(self):
        return self.request.is_admin or bool(self.occasion.choices)

    @property
    def recipients(self):
        if self.send_to.data == 'myself':
            return [self.request.current_username]

        elif self.send_to.data == 'by_role':
            recipients = self.recipients_by_role(self.roles.data)

        elif self.send_to.data == 'by_occasion':
            recipients = self.recipients_by_occasion(self.occasion.data)

        elif self.send_to.data == 'with_wishlist':
            recipients = self.recipients_with_wishes()

        elif self.send_to.data == 'with_bookings':
            recipients = self.recipients_with_bookings()

        elif self.send_to.data == 'active_organisers':
            recipients = self.recipients_which_are_active_organisers()

        elif self.send_to.data == 'with_unpaid_bills':
            recipients = self.recipients_with_unpaid_bills()

        else:
            raise NotImplementedError

        return [r for r in recipients if r in self.recipients_pool]

    @property
    def recipients_pool(self):
        users = UserCollection(self.request.app.session())
        users = users.query()

        if self.state.data == ['active']:
            users = users.filter(User.active == True)
        elif self.state.data == ['inactive']:
            users = users.filter(User.active == False)
        elif self.state.data != ['active', 'inactive']:
            return set()

        return set(u.username for u in users.with_entities(User.username))

    def recipients_by_role(self, roles):
        if not roles:
            return []

        users = UserCollection(self.request.app.session())

        q = users.by_roles(*roles)
        q = q.filter(User.active == True)
        q = q.with_entities(User.username)

        return [u.username for u in q]

    def recipients_with_wishes(self):
        bookings = BookingCollection(self.request.app.session())
        period = self.request.app.active_period

        if not period.wishlist_phase:
            return []

        q = bookings.query()
        q = q.join(Period)

        q = q.filter(Period.active == True)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return [b.username for b in q]

    def recipients_with_bookings(self):
        bookings = BookingCollection(self.request.app.session())
        period = self.request.app.active_period

        if period.wishlist_phase:
            return []

        q = bookings.query()
        q = q.join(Period)

        q = q.filter(Period.active == True)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return [b.username for b in q]

    def recipients_which_are_active_organisers(self):
        occasions = OccasionCollection(self.request.app.session())

        q = occasions.query()
        q = q.join(Activity)
        q = q.join(Period)
        q = q.filter(Period.active == True)

        q = q.with_entities(distinct(Activity.username).label('username'))

        return [o.username for o in q]

    def recipients_with_unpaid_bills(self):
        period = self.request.app.active_period
        billing = BillingCollection(self.request.app.session(), period)

        return [
            username for username, bill in billing.bills.items()
            if not bill.paid
        ]

    def recipients_by_occasion_query(self, occasions):
        bookings = BookingCollection(self.request.app.session())

        q = bookings.query()
        q = q.join(Period)
        q = q.join(Booking.occasion)
        if occasions:
            q = q.filter(Booking.occasion_id.in_(occasions))
        else:
            q = q.filter(Booking.occasion_id == uuid4())
        q = q.filter(or_(
            and_(Occasion.cancelled == False, Booking.state == 'accepted'),
            and_(Occasion.cancelled == True, Booking.state == 'cancelled')
        ))
        q = q.filter(Period.active == True)
        q = q.filter(Period.confirmed == True)

        return q

    def recipients_by_occasion(self, occasions):
        q = self.recipients_by_occasion_query(occasions)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return [b.username for b in q]

    def recipients_count_by_occasion(self, occasions):
        q = self.recipients_by_occasion_query(occasions)
        q = q.with_entities(
            Booking.occasion_id,
            func.count(Booking.occasion_id).label('count')
        )
        q = q.group_by(Booking.occasion_id)
        return {r.occasion_id: r.count for r in q}

    def populate_occasion(self):
        q = OccasionCollection(self.request.app.session()).query()
        q = q.join(Activity)
        q = q.join(Period)
        q = q.filter(Period.active == True)
        q = q.order_by(Activity.name, Occasion.order)

        layout = DefaultLayout(self.model, self.request)

        occasions = tuple(q)
        recipients = self.recipients_count_by_occasion(
            [o.id for o in occasions]
        )

        def choice(occasion):
            if occasion.cancelled:
                template = _(
                    "${title} (cancelled) "
                    "<small>${dates}, ${count} Attendees</small>"
                )
            else:
                template = _(
                    "${title} "
                    "<small>${dates}, ${count} Attendees</small>"
                )

            return occasion.id.hex, self.request.translate(_(
                template,
                mapping={
                    'title': occasion.activity.title,
                    'dates': ', '.join(
                        layout.format_datetime_range(
                            d.localized_start,
                            d.localized_end
                        ) for d in occasion.dates
                    ),
                    'count': recipients.get(occasion.id, 0)
                }
            ))

        assert not self.occasion.choices
        self.occasion.choices = [choice(o) for o in occasions]
