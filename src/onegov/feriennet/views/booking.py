from __future__ import annotations

import morepath
import urllib.parse

from collections import defaultdict, OrderedDict
from datetime import date
from decimal import Decimal
from markupsafe import Markup
from onegov.activity import Activity, AttendeeCollection
from onegov.activity import Attendee
from onegov.activity import Booking
from onegov.activity import BookingCollection
from onegov.activity import Occasion
from onegov.core.custom import json
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.orm import as_selectable_from_path
from onegov.core.security import Public, Personal, Secret
from onegov.core.templates import render_macro, render_template
from onegov.core.utils import normalize_for_url, module_path
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import (
    BookingCollectionLayout, DefaultLayout, GroupInviteLayout)
from onegov.feriennet.models import AttendeeCalendar, GroupInvite
from onegov.feriennet.utils import decode_name
from onegov.feriennet.views.shared import users_for_select_element
from onegov.town6.layout import DefaultMailLayout
from onegov.user import User
from purl import URL
from sortedcontainers import SortedList
from sqlalchemy import select, and_, not_
from sqlalchemy.orm import contains_eager
from uuid import UUID


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from onegov.activity.models import BookingPeriod, BookingPeriodMeta
    from onegov.activity.models.booking import BookingState
    from onegov.core.elements import Trait
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from sqlalchemy.orm import Query, Session
    from typing import NamedTuple
    from webob import Response

    class RelatedAttendeeRow(NamedTuple):
        occasion_id: UUID
        attendee_count: int
        parent: str
        parent_username: str
        children: int
        phone: str | None
        place: str | None
        email: str
        booking_state: BookingState


DELETABLE_STATES = ('open', 'cancelled', 'denied', 'blocked')


def all_bookings(collection: BookingCollection) -> list[Booking]:
    """ Loads all bookings together with the linked occasions, attendees and
    activities. This is somewhat of a heavy query, but it beats having to
    load all these things separately.

    """
    query = collection.query()

    query = query.join(Booking.attendee)
    query = query.join(Booking.occasion)
    query = query.join(Occasion.activity)

    query = query.options(contains_eager(Booking.attendee))
    query = query.options(
        contains_eager(Booking.occasion).
        contains_eager(Occasion.activity))

    query = query.order_by(Booking.attendee_id)
    query = query.order_by(Activity.name)
    query = query.order_by(Occasion.order)

    return query.all()


def group_bookings(
    period: BookingPeriod | BookingPeriodMeta,
    bookings: Iterable[Booking]
) -> dict[Attendee, dict[BookingState, SortedList[Booking]]]:
    """ Takes a (small) list of bookings and groups them by attendee and state
    and sorting them by date.

    """

    state_order = (
        'open',
        'accepted',
        'denied',
        'blocked',
        'cancelled'
    )

    if period.wishlist_phase:
        def state(booking: Booking) -> BookingState:
            return 'open'
    else:
        def state(booking: Booking) -> BookingState:
            return booking.state

    grouped: dict[Attendee, dict[BookingState, SortedList[Booking]]] = {}

    for b in sorted(bookings, key=lambda b: state_order.index(state(b))):

        if b.attendee not in grouped:
            # I tried using a SortedDict here, but chameleon has problems
            # dealing with it, so an ordered dict is used instead
            grouped[b.attendee] = OrderedDict()

        if state(b) not in grouped[b.attendee]:
            grouped[b.attendee][state(b)] = SortedList(  # type:ignore
                key=lambda b: b.order)

        grouped[b.attendee][state(b)].add(b)

    return grouped


def total_by_bookings(
    period: BookingPeriod | BookingPeriodMeta | None,
    bookings: Collection[Booking]
) -> Decimal:

    if bookings:
        total = sum(
            b.cost for b in bookings
            if b.state == 'accepted' and b.cost
        )
        total = total or Decimal('0.00')
    else:
        return Decimal('0.00')

    if period and period.all_inclusive and period.booking_cost:
        total += period.booking_cost

    return total


def related_attendees(
    session: Session,
    occasion_ids: Collection[UUID]
) -> dict[UUID, list[RelatedAttendeeRow]]:

    stmt = as_selectable_from_path(
        module_path('onegov.feriennet', 'queries/related_attendees.sql'))

    related: Query[RelatedAttendeeRow] = session.execute(
        select(stmt.c).where(
            and_(
                stmt.c.occasion_id.in_(occasion_ids),
                stmt.c.booking_state == 'accepted'
            )
        )
    )

    result = defaultdict(list)

    for r in related:
        result[r.occasion_id].append(r)

    return result


def attendees_by_username(
    request: FeriennetRequest,
    username: str
) -> list[Attendee]:
    """ Loads the given attendees linked to the given username, sorted by
    their name.

    """

    a = AttendeeCollection(request.session).by_username(username).all()
    a.sort(key=lambda a: normalize_for_url(a.name))

    return a


def get_booking_title(layout: DefaultLayout, booking: Booking) -> str:
    return '{} - {}'.format(
        booking.occasion.activity.title,
        layout.format_datetime_range(
            booking.occasion.dates[0].localized_start,
            booking.occasion.dates[0].localized_end))


def actions_by_booking(
    layout: DefaultLayout,
    period: BookingPeriod | BookingPeriodMeta | None,
    booking: Booking
) -> list[Link]:

    actions: list[Link] = []

    if not period:
        return actions

    if period.wishlist_phase or booking.state in ('accepted', 'open'):
        if period.wishlist_phase or period.booking_phase:
            if not booking.group_code:
                actions.append(
                    Link(
                        text=_('Invite a companion'),
                        url=layout.request.link(booking, 'invite'),
                        attrs={
                            'class': 'invite-link',
                        },
                    )
                )
            else:
                # XXX this is not too efficient as there might be many queries
                states: Literal['*'] | tuple[BookingState, ...]
                if period.wishlist_phase:
                    states = '*'
                else:
                    states = ('open', 'accepted')

                count = booking.group_code_count(states) - 1

                invite = GroupInvite(
                    layout.request.session,
                    booking.group_code,
                    booking.username)

                if count < 1:

                    # the group code is not shown if the attendee is alone
                    actions.append(
                        Link(
                            text=_('Invite a companion'),
                            url=layout.request.link(invite),
                            attrs={
                                'class': 'invite-link',
                            },
                        )
                    )
                elif count == 1:
                    actions.append(
                        Link(
                            text=_('With 1 companion in a group'),
                            url=layout.request.link(invite),
                            attrs={
                                'class': 'invite-link',
                                'data-group': booking.group_code,
                            },
                        )
                    )
                elif count > 1:
                    actions.append(
                        Link(
                            text=_('With ${n} companions in a group', mapping={
                                'n': count
                            }),
                            url=layout.request.link(invite),
                            attrs={
                                'class': 'invite-link',
                                'data-group': booking.group_code,
                            },
                        )
                    )

    if period.wishlist_phase or (
            booking.state in DELETABLE_STATES and not period.finalized):

        label = (
            period.wishlist_phase
            and _('Remove wish')
            or _('Remove booking')
        )

        actions.append(Link(
            text=label,
            url=layout.csrf_protected_url(layout.request.link(booking)),
            attrs={
                'class': 'delete-link',
            },
            traits=(
                Confirm(
                    _('Do you really want to remove "${title}"?', mapping={
                        'title': get_booking_title(layout, booking)
                    }),
                    None,
                    label,
                    _('Cancel'),
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=layout.request.link(layout.model),
                    target='#booking-{}'.format(booking.id),
                ),
            )
        ))

    if period.active and period.confirmed and booking.state == 'accepted':
        if (
            # admins can always cancel bookings
            layout.request.is_admin
            # other users can if it isn't past its cancellation deadline
            or not booking.occasion.is_past_cancellation(layout.today())
        ):
            actions.append(Link(
                text=_('Cancel Booking'),
                url=layout.csrf_protected_url(
                    layout.request.link(booking, 'cancel')
                ),
                attrs={
                    'class': 'cancel-link',
                },
                traits=(
                    Confirm(
                        _('Do you really want to cancel "${title}"?', mapping={
                            'title': get_booking_title(layout, booking)
                        }),
                        _('This cannot be undone.'),
                        _('Cancel Booking'),
                        _('Cancel'),
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=layout.request.link(layout.model)
                    )
                )))

    return actions


def show_error_on_attendee(
    request: FeriennetRequest,
    attendee: Attendee,
    message: str
) -> None:

    @request.after
    def show_error(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'show-alert')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'type': 'alert',
            'target': f'#alert-boxes-for-{attendee.id}',
            'message': request.translate(message)
        }, ensure_ascii=True))


@FeriennetApp.html(
    model=BookingCollection,
    template='bookings.pt',
    permission=Personal)
def view_my_bookings(
    self: BookingCollection,
    request: FeriennetRequest
) -> RenderData:

    assert self.username is not None
    attendees = attendees_by_username(request, self.username)

    periods = request.app.periods
    period = next((p for p in periods if p.id == self.period_id), None)

    bookings = all_bookings(self)
    grouped_bookings = period and group_bookings(period, bookings) or {}

    related = request.app.org.meta.get('show_related_contacts') or None

    if period and period.confirmed and related:
        related = related_attendees(self.session, occasion_ids={
            b.occasion_id for b in bookings
        })
    else:
        related = None

    if request.is_admin:
        users = users_for_select_element(request)
        user = (request.session.query(User)
                .filter_by(username=self.username).one())
    else:
        assert request.current_user is not None
        users, user = None, request.current_user

    def subscribe_link(attendee: Attendee) -> str:
        url = request.link(AttendeeCalendar(self.session, attendee))
        url = url.replace('https://', 'webcal://')
        url = url.replace('http://', 'webcal://')

        return url

    def get_total(attendee: Attendee) -> Decimal:
        bookings = tuple(
            b for state in grouped_bookings[attendee]
            for b in grouped_bookings[attendee][state]
        )

        return total_by_bookings(period, bookings)

    def booking_cost(booking: Booking) -> Decimal | None:
        if period and period.confirmed:
            return booking.cost
        else:
            return booking.occasion.total_cost

    has_emergency_contact = user.data and user.data.get('emergency')
    show_emergency_info = user.username == request.current_username

    layout = BookingCollectionLayout(self, request, user)

    def user_select_link(user: User) -> str:
        return request.class_link(BookingCollection, {
            'username': user.username,
            'period_id': period and period.id or None
        })

    def occasion_attendees(
        request: FeriennetRequest,
        username: str,
        occasion_id: UUID
    ) -> list[Attendee]:

        children = attendees_by_username(request, username)
        attendees = []
        for c in children:
            accepted_bookings = [
                b for b in c.bookings if b.state == 'accepted']
            occasions = [b.occasion_id for b in accepted_bookings]
            if occasion_id in occasions:
                attendees.append(c)

        return attendees

    return {
        'actions_by_booking': lambda b: actions_by_booking(layout, period, b),
        'attendees': attendees,
        'occasion_attendees': occasion_attendees,
        'subscribe_link': subscribe_link,
        'grouped_bookings': grouped_bookings,
        'total_by_attendee': get_total,
        'has_bookings': bookings and True or False,
        'booking_cost': booking_cost,
        'layout': layout,
        'model': self,
        'period': period,
        'periods': periods,
        'related': related,
        'user': user,
        'users': users,
        'user_select_link': user_select_link,
        'title': layout.title,
        'has_emergency_contact': has_emergency_contact,
        'show_emergency_info': show_emergency_info
    }


@FeriennetApp.view(
    model=Booking,
    permission=Personal,
    request_method='DELETE')
def delete_booking(self: Booking, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    if self.period.confirmed and self.state not in DELETABLE_STATES:
        show_error_on_attendee(request, self.attendee, _(
            'Only open, cancelled, denied or blocked bookings may be deleted'))

        return

    BookingCollection(request.session).delete(self)

    @request.after
    def remove_target(response: Response) -> None:
        response.headers.add('X-IC-Remove', 'true')


@FeriennetApp.view(
    model=Booking,
    name='cancel',
    permission=Personal,
    request_method='POST')
def cancel_booking(self: Booking, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    if not self.period.wishlist_phase:
        if not request.is_admin:
            if self.occasion.is_past_cancellation(date.today()):
                request.alert(_(
                    'Only admins may cancel bookings at this point.'
                ))

                return

    BookingCollection(request.session).cancel_booking(
        booking=self,
        score_function=self.period.scoring,
        cascade=False)

    request.success(_('The booking was cancelled successfully'))

    bookings_link = Markup('<a href="{}">{}</a>').format(
        request.class_link(BookingCollection, {
            'period_id': self.period.id
        }),
        request.translate(_('Bookings'))
    )

    subject = request.translate(_(
        'Degregistration of ${attendee} for "${title}"',
        mapping={
            'title': self.occasion.activity.title,
            'attendee': self.attendee.name
        }))

    if self.period.booking_start <= date.today():
        request.app.send_transactional_email(
            subject=subject,
            receivers=(self.user.username, ),
            content=render_template('mail_booking_canceled.pt', request, {
                'layout': DefaultMailLayout(self, request),
                'title': subject,
                'model': self,
                'bookings_link': bookings_link,
                'name': self.attendee.name,
                'dates': self.dates
            })
        )

    @request.after
    def update_matching(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'reload-from')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'selector': f'#{self.occasion.id}'
        }))


@FeriennetApp.view(
    model=Booking,
    name='toggle-star',
    permission=Personal,
    request_method='POST')
def toggle_star(self: Booking, request: FeriennetRequest) -> str:

    if self.period.wishlist_phase:
        if not self.starred:
            if not self.star(max_stars=3):
                show_error_on_attendee(request, self.attendee, _(
                    'Cannot select more than three favorites per child'))
        else:
            self.unstar()
    else:
        show_error_on_attendee(request, self.attendee, _(
            'The period is not in the wishlist-phase'))

    layout = DefaultLayout(self, request)
    return render_macro(layout.macros['star'], request, {'booking': self})


@FeriennetApp.view(
    model=Booking,
    name='toggle-nobble',
    permission=Secret,
    request_method='POST')
def toggle_nobble(self: Booking, request: FeriennetRequest) -> str:
    if self.nobbled:
        self.unnobble()
    else:
        self.nobble()

    layout = DefaultLayout(self, request)
    return render_macro(layout.macros['nobble'], request, {'booking': self})


def render_css(content: str, request: FeriennetRequest) -> morepath.Response:
    response = morepath.Response(content)
    response.content_type = 'text/css'
    return response


@FeriennetApp.view(
    model=BookingCollection,
    name='mask',
    permission=Personal,
    render=render_css)
def view_mask(self: BookingCollection, request: FeriennetRequest) -> str:
    # hackish way to get the single attendee print to work -> mask all the
    # attendees, except for the one given by param

    try:
        attendee = UUID(request.params.get('id', None)).hex  # type:ignore
    except (ValueError, TypeError):
        return ''

    return f"""
        .attendee-bookings-row {{
            display: none;
        }}

        #attendee-{attendee} {{
            display: block;
        }}
    """


@FeriennetApp.view(
    model=Booking,
    name='invite',
    permission=Personal)
def create_invite(self: Booking, request: FeriennetRequest) -> Response:
    """ Creates a group_code on the booking, if one doesn't exist already
    and redirects to the GroupInvite view.

    """

    if not self.group_code:
        self.group_code = GroupInvite.create(
            request.session, self.username).group_code

    link = request.link(GroupInvite(
        request.session, self.group_code, self.username))

    return request.redirect(link)


@FeriennetApp.html(
    model=GroupInvite,
    permission=Public,
    template='invite.pt')
def view_group_invite(
    self: GroupInvite,
    request: FeriennetRequest
) -> RenderData:

    layout = GroupInviteLayout(self, request)
    occasion = self.occasion
    attendees_count = len(self.attendees)

    existing = [a for a, b in self.attendees if a.username == self.username]
    external = [a for a, b in self.attendees if a.username != self.username]
    possible = (
        request.session.query(Attendee)
        .filter_by(username=self.username)
        .filter(not_(Attendee.id.in_(tuple(a.id for a in existing))))
        .all()
    )

    actionable_bookings = {
        b.attendee_id: b for b in request.session.query(Booking).filter_by(
            username=self.username,
            occasion_id=occasion.id,
        )
    }

    def signup_url(attendee: Attendee | None = None) -> str:
        # we need a logged in user
        if not request.is_logged_in:
            return layout.login_to_url(request.link(self))

        # build the URL needed to book the occasion
        url = request.link(occasion, name='book')

        # preselect the attendee when booking the occasion, and join this group
        if attendee:
            url_obj = URL(url).query_param('attendee_id', attendee.id.hex)
        else:
            url_obj = URL(url).query_param('attendee_id', 'other')

        # preselect the group code and the username
        url_obj = url_obj.query_param('group_code', self.group_code)

        if self.username is not None:
            url_obj = url_obj.query_param('username', self.username)

        url = url_obj.as_string()

        # return to the current URL
        url = request.return_here(url)

        return url

    def group_action(
        attendee: Attendee,
        action: Literal['join', 'leave']
    ) -> Link:

        assert action in ('join', 'leave')

        traits: tuple[Trait, ...]
        if attendees_count == 1 and action == 'leave':
            traits = (
                Intercooler(
                    request_method='POST',
                    redirect_after=request.class_link(BookingCollection)
                ),
            )
        else:
            traits = (
                Intercooler(
                    request_method='POST',
                    redirect_after=request.link(self)
                ),
            )

        if attendee.id in actionable_bookings:
            booking = actionable_bookings[attendee.id]

            url = (URL(request.link(self, action))
                   .query_param('booking_id', booking.id.hex)
                   .as_string())
        else:
            url = signup_url(attendee)
            traits = ()

        if action == 'join':
            text = _('add to group')
            icon = 'plus-icon'
        else:
            text = _('remove from group')
            icon = 'minus-icon'

        return Link(
            text=text,
            url=layout.csrf_protected_url(url),
            traits=traits,
            attrs={'class': (icon, 'before')}
        )

    # https://stackoverflow.com/a/23847977/138103
    first_child = existing and existing[0] or external[0]
    first_name = decode_name(first_child.name)[0]
    subject = occasion.activity.title
    message = _(
        (
            'Hi!\n\n'
            '${first_name} wants to take part in the "${title}" activity by '
            '${organisation} and would be thrilled to go with a mate.\n\n'
            'You can add the activity to the wishlist of your child through '
            'the following link, if you are interested. This way the children '
            'have a better chance of getting a spot together:\n\n'
            '${link}'
        ), mapping={
            'first_name': first_name,
            'link': request.link(self.for_username(None)),
            'title': occasion.activity.title,
            'organisation': request.app.org.name,
        }
    )

    mailto = 'mailto:%20?subject={subject}&body={message}'.format(
        subject=urllib.parse.quote(subject),
        message=urllib.parse.quote(request.translate(message))
    )

    users = users_for_select_element(request)
    user = (request.session.query(User)
            .filter_by(username=self.username).first())

    def user_select_link(user: User) -> str:
        return request.link(self.for_username(user.username))

    return {
        'layout': layout,
        'title': _('Group'),
        'occasion': occasion,
        'model': self,
        'group_action': group_action,
        'signup_url': signup_url,
        'existing': existing,
        'external': external,
        'possible': possible,
        'mailto': mailto,
        'users': users,
        'user': user,
        'user_select_link': user_select_link,
    }


@FeriennetApp.view(
    model=GroupInvite,
    permission=Personal,
    name='join',
    request_method='POST')
def join_group(self: GroupInvite, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    booking_id = request.params.get('booking_id', None)
    booking = request.session.query(Booking).filter_by(id=booking_id).first()

    if not booking:
        request.warning(_('The booking does not exist'))
        return

    own_children = {
        a_id for a_id, in request.session.query(Attendee.id)
        .filter_by(username=self.username)
    }
    if booking.attendee_id not in own_children:
        request.alert(
            _('Not permitted to join this attendee to the group'))
        return

    booking.group_code = self.group_code
    request.success(_('Successfully joined the group'))


@FeriennetApp.view(
    model=GroupInvite,
    permission=Personal,
    name='leave',
    request_method='POST')
def leave_group(self: GroupInvite, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    booking_id = request.params.get('booking_id', None)
    booking = request.session.query(Booking).filter_by(id=booking_id).first()

    if not booking:
        request.warning(_('The booking does not exist'))
        return

    own_children = {
        a_id for a_id, in request.session.query(Attendee.id)
        .filter_by(username=self.username)
    }

    if booking.attendee_id not in own_children:
        request.alert(
            _('Not permitted to evict this attendee from the group'))
        return

    booking.group_code = None
    request.success(_('Successfully left the group'))
