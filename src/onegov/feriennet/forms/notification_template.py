from __future__ import annotations

from functools import cached_property
from markupsafe import Markup, escape

from onegov.activity import Activity
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet import _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.models import NotificationTemplate
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField, HtmlField
from onegov.user import User, UserCollection
from sqlalchemy import distinct, or_, and_, select, exists
from uuid import uuid4
from wtforms.fields import BooleanField, StringField, RadioField
from wtforms.validators import InputRequired, ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from onegov.activity.models import BookingPeriodMeta
    from onegov.feriennet.request import FeriennetRequest
    from sqlalchemy.orm import Query


class NotificationTemplateForm(Form):

    subject = StringField(
        label=_('Subject'),
        validators=[InputRequired()]
    )

    text = HtmlField(
        label=_('Message'),
        validators=[InputRequired()],
        render_kw={'rows': 12}
    )

    def validate_subject(self, field: StringField) -> None:
        if not self.subject.data:   # caught by input required
            return

        c = exists().where(NotificationTemplate.subject == self.subject.data)

        # in edit mode we must exclude the current model
        if isinstance(self.model, NotificationTemplate):
            c = c.where(NotificationTemplate.id != self.model.id)

        if self.request.session.query(c).scalar():
            raise ValidationError(
                _('A notification with this subject exists already')
            )


class NotificationTemplateSendForm(Form):

    request: FeriennetRequest

    send_to = RadioField(
        label=_('Send to'),
        choices=[
            ('myself', _(
                'Myself'
            )),
            ('active_organisers', _(
                'Organisers with an occasion'
            )),
            ('by_role', _(
                'Users of a given role'
            )),
            ('with_wishlist', _(
                'Users with wishes'
            )),
            ('with_accepted_bookings', _(
                'Users with accepted bookings'
            )),
            ('with_unpaid_bills', _(
                'Users with unpaid bills'
            )),
            ('by_occasion', _(
                'Users with attenedees that have an occasion on their '
                'wish- or booking-list'
            )),
        ],
        default='by_role'
    )

    roles = MultiCheckboxField(
        label=_('Role'),
        choices=[
            ('admin', _('Administrators')),
            ('editor', _('Organisers')),
            ('member', _('Members'))
        ],
        depends_on=('send_to', 'by_role')
    )

    occasion = MultiCheckboxField(
        label=_('Occasion'),
        choices=None,
        depends_on=('send_to', 'by_occasion')
    )

    state = MultiCheckboxField(
        label=_('Useraccounts'),
        choices=[
            ('active', _('Active users')),
            ('inactive', _('Inactive users')),
        ],
        default=['active'],
    )

    no_spam = BooleanField(
        label=_(
            'I hereby confirm that this message is relevant to the '
            'recipients and is not spam.'
        ),
        render_kw={'force_simple': True},
        validators=[InputRequired()]
    )

    def on_request(self) -> None:
        self.occasion.choices = list(self.occasion_choices)

    @cached_property
    def period(self) -> BookingPeriodMeta:
        for period in self.request.app.periods:
            if period.id == self.model.period_id:
                return period
        raise AssertionError('unreachable')

    @property
    def has_choices(self) -> bool:
        return self.request.is_admin or bool(self.occasion.choices)

    @property
    def recipients(self) -> set[str]:
        if self.send_to.data == 'myself':
            assert self.request.current_username is not None
            return {self.request.current_username}

        elif self.send_to.data == 'by_role':
            recipients = self.recipients_by_role(self.roles.data or ())

        elif self.send_to.data == 'by_occasion':
            recipients = self.recipients_by_occasion(self.occasion.data or ())

        elif self.send_to.data == 'with_wishlist':
            recipients = self.recipients_with_wishes()

        elif self.send_to.data == 'with_accepted_bookings':
            recipients = self.recipients_with_accepted_bookings()

        elif self.send_to.data == 'active_organisers':
            recipients = self.recipients_which_are_active_organisers()

        elif self.send_to.data == 'with_unpaid_bills':
            recipients = self.recipients_with_unpaid_bills()

        else:
            raise NotImplementedError

        return recipients & self.recipients_pool

    @property
    def recipients_pool(self) -> set[str]:
        users = UserCollection(self.request.session).query()

        if self.state.data == ['active']:
            users = users.filter(User.active == True)
        elif self.state.data == ['inactive']:
            users = users.filter(User.active == False)
        elif self.state.data != ['active', 'inactive']:
            return set()

        return {u.username for u in users.with_entities(User.username)}

    def recipients_by_role(self, roles: Collection[str]) -> set[str]:
        if not roles:
            return set()

        q = UserCollection(self.request.session).by_roles(*roles)
        q = q.with_entities(User.username)

        return {u.username for u in q}

    def recipients_with_wishes(self) -> set[str]:
        bookings = BookingCollection(self.request.session)

        if not self.period.wishlist_phase:
            return set()

        q = bookings.query().order_by(None)
        q = q.filter_by(period_id=self.period.id)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return {b.username for b in q}

    def recipients_with_accepted_bookings(self) -> set[str]:
        bookings = BookingCollection(self.request.session)

        if self.period.wishlist_phase:
            return set()

        q = bookings.query().order_by(None)
        q = q.filter_by(
            period_id=self.period.id,
            state='accepted')

        q = q.with_entities(distinct(Booking.username).label('username'))

        return {b.username for b in q}

    def recipients_which_are_active_organisers(self) -> set[str]:
        occasions = OccasionCollection(self.request.session)

        q = occasions.query().filter_by(period_id=self.period.id)
        q = q.join(Activity)
        q = q.filter(Occasion.cancelled == False)

        uq = q.with_entities(distinct(Activity.username))

        return {username for username, in uq}

    def recipients_with_unpaid_bills(self) -> set[str]:
        billing = BillingCollection(self.request, period=self.period)

        return {
            username for username, bill in billing.bills.items()
            if not bill.paid
        }

    def recipients_by_occasion_query(
        self,
        # NOTE: We rely on SQLAlchemy auto-casting text to uuid here
        #       if we wanted to be a little bit more rigorous we could
        #       use `coerce` on `MultiCheckboxField` to ensure we're
        #       passing in `UUID`s, rather than `str`s.
        occasions: Collection[str]
    ) -> Query[Booking]:
        bookings = BookingCollection(self.request.session)

        q = bookings.query().order_by(None)
        q = q.filter_by(period_id=self.period.id)
        q = q.join(Booking.occasion)

        if not occasions:
            # results in an impossible query that returns no results
            return q.filter(Booking.occasion_id == uuid4())

        q = q.filter(Booking.occasion_id.in_(occasions))

        if self.period.confirmed:
            q = q.filter(or_(
                and_(Occasion.cancelled == False, Booking.state == 'accepted'),
                and_(Occasion.cancelled == True, Booking.state == 'cancelled'),
            ))

        return q

    def recipients_by_occasion(
        self,
        occasions: Collection[str],
        include_organisers: bool = True
    ) -> set[str]:

        q = self.recipients_by_occasion_query(occasions)
        q = q.with_entities(distinct(Booking.username).label('username'))

        attendees = {r.username for r in q}

        if not include_organisers:
            return attendees

        q2 = OccasionCollection(self.request.session).query()
        q2 = q2.join(Activity)
        q2 = q2.filter(Occasion.id.in_(occasions))
        uq = q2.with_entities(distinct(Activity.username))

        organisers = {username for username, in uq}

        return attendees | organisers

    @property
    def occasion_choices(self) -> Iterator[tuple[str, Markup]]:
        layout = DefaultLayout(self.model, self.request)

        stmt = as_selectable_from_path(
            module_path(
                'onegov.feriennet',
                'queries/occasion_choices.sql'
            )
        )

        query = select(*stmt.c).where(
            stmt.c.period_id == self.period.id
        )

        templates = {
            True: _(
                '${title} (cancelled) '
                '<small>${dates}, ${count} Attendees</small>',
                markup=True
            ),
            False: _(
                '${title} '
                '<small>${dates}, ${count} Attendees</small>',
                markup=True
            )
        }

        for record in self.request.session.execute(query):
            template = templates[record.cancelled]
            label = self.request.translate(template % {
                'title': escape(record.title),
                'count': record.count,
                'dates': ', '.join(
                    layout.format_datetime_range(*d) for d in record.dates
                )
            })
            yield record.occasion_id.hex, label
