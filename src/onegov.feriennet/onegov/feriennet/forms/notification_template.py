from onegov.activity import Activity
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet import _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.models import NotificationTemplate
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.user import User, UserCollection
from sqlalchemy import distinct, or_, func, and_, select, exists
from uuid import uuid4
from wtforms.fields import StringField, TextAreaField, RadioField, SelectField
from wtforms.validators import InputRequired


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

    def ensure_not_duplicate_subject(self):
        c = exists().where(NotificationTemplate.subject == self.subject.data)

        # in edit mode we must exclude the current model
        if isinstance(self.model, NotificationTemplate):
            c = c.where(NotificationTemplate.id != self.model.id)

        if self.request.session.query(c).scalar():
            self.subject.errors.append(
                _("A notification with this subject exists already")
            )

            return False


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

    period = SelectField(
        label=_("Period"),
        choices=None,
        depends_on=('send_to', 'with_unpaid_bills'),
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
        self.populate_periods()

    @property
    def has_choices(self):
        return self.request.is_admin or bool(self.occasion.choices)

    @property
    def recipients(self):
        if self.send_to.data == 'myself':
            return {self.request.current_username}

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

        return recipients & self.recipients_pool

    @property
    def recipients_pool(self):
        users = UserCollection(self.request.session)
        users = users.query()

        if self.state.data == ['active']:
            users = users.filter(User.active == True)
        elif self.state.data == ['inactive']:
            users = users.filter(User.active == False)
        elif self.state.data != ['active', 'inactive']:
            return set()

        return {u.username for u in users.with_entities(User.username)}

    def recipients_by_role(self, roles):
        if not roles:
            return set()

        users = UserCollection(self.request.session)

        q = users.by_roles(*roles)
        q = q.filter(User.active == True)
        q = q.with_entities(User.username)

        return {u.username for u in q}

    def recipients_with_wishes(self):
        bookings = BookingCollection(self.request.session)
        period = self.request.app.active_period

        if not period.wishlist_phase:
            return set()

        q = bookings.query()
        q = q.join(Period)

        q = q.filter(Period.active == True)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return {b.username for b in q}

    def recipients_with_bookings(self):
        bookings = BookingCollection(self.request.session)
        period = self.request.app.active_period

        if period.wishlist_phase:
            return set()

        q = bookings.query()
        q = q.join(Period)

        q = q.filter(Period.active == True)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return {b.username for b in q}

    def recipients_which_are_active_organisers(self):
        occasions = OccasionCollection(self.request.session)

        q = occasions.query()
        q = q.join(Activity)
        q = q.join(Period)
        q = q.filter(Period.active == True)
        q = q.filter(Occasion.cancelled == False)

        q = q.with_entities(distinct(Activity.username).label('username'))

        return {o.username for o in q}

    def recipients_with_unpaid_bills(self):
        period = next((
            p for p in self.request.app.periods
            if p.id.hex == self.period.data
        ), None) or self.request.app.active_period

        billing = BillingCollection(self.request, period=period)

        return {
            username for username, bill in billing.bills.items()
            if not bill.paid
        }

    def recipients_by_occasion_query(self, occasions):
        bookings = BookingCollection(self.request.session)

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

    def recipients_by_occasion(self, occasions, include_organisers=True):
        q = self.recipients_by_occasion_query(occasions)
        q = q.with_entities(distinct(Booking.username).label('username'))

        attendees = {r.username for r in q}

        if not include_organisers:
            return attendees

        q = OccasionCollection(self.request.session).query()
        q = q.join(Activity)
        q = q.filter(Occasion.id.in_(occasions))
        q = q.with_entities(distinct(Activity.username).label('username'))

        organisers = {r.username for r in q}

        return attendees | organisers

    def recipients_count_by_occasion(self, occasions):
        q = self.recipients_by_occasion_query(occasions)
        q = q.with_entities(
            Booking.occasion_id,
            func.count(Booking.occasion_id).label('count')
        )
        q = q.group_by(Booking.occasion_id)
        return {r.occasion_id: r.count for r in q}

    @property
    def occasion_choices(self):
        if not self.request.app.active_period:
            return

        layout = DefaultLayout(self.model, self.request)

        stmt = as_selectable_from_path(
            module_path(
                'onegov.feriennet',
                'queries/occasion_choices.sql'
            )
        )

        query = select(stmt.c).where(
            stmt.c.period_id == self.request.app.active_period.id
        )

        templates = {
            True: _(
                "${title} (cancelled) "
                "<small>${dates}, ${count} Attendees</small>"
            ),
            False: _(
                "${title} "
                "<small>${dates}, ${count} Attendees</small>"
            )
        }

        for record in self.request.session.execute(query):
            template = templates[record.cancelled]
            label = self.request.translate(_(template, mapping={
                'title': record.title,
                'count': record.count,
                'dates': ', '.join(
                    layout.format_datetime_range(*d) for d in record.dates
                )
            }))

            yield record.occasion_id.hex, label

    def populate_periods(self):
        periods = [p for p in self.request.app.periods]
        periods.sort(key=lambda p: not p.active)

        self.period.choices = [(p.id.hex, p.title) for p in periods]

    def populate_occasion(self):
        self.occasion.choices = list(self.occasion_choices)
