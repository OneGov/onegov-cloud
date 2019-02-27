import morepath

from collections import defaultdict, OrderedDict
from datetime import date
from decimal import Decimal
from onegov.activity import Activity, AttendeeCollection
from onegov.activity import Attendee
from onegov.activity import Booking
from onegov.activity import BookingCollection
from onegov.activity import Occasion
from onegov.core.custom import json
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.orm import as_selectable_from_path
from onegov.core.security import Public, Personal, Secret
from onegov.core.templates import render_macro
from onegov.core.utils import normalize_for_url, module_path
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import BookingCollectionLayout, GroupInviteLayout
from onegov.feriennet.models import AttendeeCalendar, GroupInvite
from onegov.feriennet.views.shared import users_for_select_element
from onegov.user import User
from purl import URL
from sortedcontainers import SortedList
from sqlalchemy import select, and_
from sqlalchemy.orm import contains_eager
from uuid import UUID


DELETABLE_STATES = ('open', 'cancelled', 'denied', 'blocked')


def all_bookings(collection):
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


def group_bookings(period, bookings):
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
        def state(booking):
            return 'open'
    else:
        def state(booking):
            return booking.state

    grouped = {}

    for b in sorted(bookings, key=lambda b: state_order.index(state(b))):

        if b.attendee not in grouped:
            # I tried using a SortedDict here, but chameleon has problems
            # dealing with it, so an ordered dict is used instead
            grouped[b.attendee] = OrderedDict()

        if state(b) not in grouped[b.attendee]:
            grouped[b.attendee][state(b)] = SortedList(key=lambda b: b.order)

        grouped[b.attendee][state(b)].add(b)

    return grouped


def total_by_bookings(period, bookings):
    if bookings:
        total = sum(
            b.cost for b in bookings
            if b.state == 'accepted' and b.cost
        )
        total = total or Decimal("0.00")
    else:
        return Decimal("0.00")

    if period.all_inclusive and period.booking_cost:
        total += period.booking_cost

    return total


def related_attendees(session, occasion_ids):
    stmt = as_selectable_from_path(
        module_path('onegov.feriennet', 'queries/related_attendees.sql'))

    related = session.execute(
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


def attendees_by_username(request, username):
    """ Loads the given attendees linked to the given username, sorted by
    their name.

    """

    a = AttendeeCollection(request.session).by_username(username).all()
    a.sort(key=lambda a: normalize_for_url(a.name))

    return a


def get_booking_title(layout, booking):
    return "{} - {}".format(
        booking.occasion.activity.title,
        layout.format_datetime_range(
            booking.occasion.dates[0].localized_start,
            booking.occasion.dates[0].localized_end))


def actions_by_booking(layout, period, booking):
    actions = []

    if not period:
        return actions

    if period.wishlist_phase or booking.state in ('accepted', 'open'):
        if period.wishlist_phase or period.booking_phase:
            if not booking.group_code:
                actions.append(
                    Link(
                        text=_("Invite a companion"),
                        url=layout.request.link(booking, 'invite'),
                        attrs={
                            'class': 'invite-link',
                        },
                    )
                )
            else:
                # XXX this is not too efficient as there might be many queries
                if period.wishlist_phase:
                    states = '*'
                else:
                    states = ('open', 'accepted')

                count = booking.group_code_count(states) - 1

                invite = GroupInvite(
                    layout.request.session, booking.group_code)

                if count < 1:

                    # the group code is not shown if the attendee is alone
                    actions.append(
                        Link(
                            text=_("Invite a companion"),
                            url=layout.request.link(invite),
                            attrs={
                                'class': 'invite-link',
                            },
                        )
                    )
                elif count == 1:
                    actions.append(
                        Link(
                            text=_("With 1 companion in a group"),
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
                            text=_("With ${n} companions in a group", mapping={
                                'n': count
                            }),
                            url=layout.request.link(invite),
                            attrs={
                                'class': 'invite-link',
                                'data-group': booking.group_code,
                            },
                        )
                    )

    if period.wishlist_phase or booking.state in DELETABLE_STATES:
        label = (
            period.wishlist_phase
            and _("Remove wish")
            or _("Remove booking")
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
                    _("Cancel"),
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=layout.request.link(layout.model),
                    target='#booking-{}'.format(booking.id),
                ),
            )
        ))

    if period.booking_phase and booking.state == 'accepted':
        if layout.request.is_admin:
            may_cancel = True
        elif not booking.occasion.is_past_cancellation(layout.today()):
            may_cancel = True
        else:
            may_cancel = False

        if may_cancel:
            actions.append(Link(
                text=_("Cancel Booking"),
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
                        _("This cannot be undone."),
                        _("Cancel Booking"),
                        _("Cancel"),
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=layout.request.link(layout.model)
                    )
                )))

    return actions


def show_error_on_attendee(request, attendee, message):
    @request.after
    def show_error(response):
        response.headers.add('X-IC-Trigger', 'show-alert')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'type': 'alert',
            'target': '#alert-boxes-for-{}'.format(attendee.id),
            'message': request.translate(message)
        }))


@FeriennetApp.html(
    model=BookingCollection,
    template='bookings.pt',
    permission=Personal)
def view_my_bookings(self, request):
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
        user = request.session.query(User)\
            .filter_by(username=self.username).first()
    else:
        users, user = None, request.current_user

    def subscribe_link(attendee):
        url = request.link(AttendeeCalendar(self.session, attendee))
        url = url.replace('https://', 'webcal://')
        url = url.replace('http://', 'webcal://')

        return url

    def get_total(attendee):
        bookings = (
            b for state in grouped_bookings[attendee]
            for b in grouped_bookings[attendee][state]
        )

        return total_by_bookings(period, bookings)

    def booking_cost(booking):
        if period.confirmed:
            return booking.cost
        else:
            base_cost = 0 if period.all_inclusive else period.booking_cost
            return (booking.occasion.cost or 0) + (base_cost or 0)

    has_emergency_contact = user.data and user.data.get('emergency')
    show_emergency_info = user.username == request.current_username

    layout = BookingCollectionLayout(self, request, user)

    def user_select_link(user):
        return request.class_link(BookingCollection, {
            'username': user.username,
            'period_id': period and period.id or None
        })

    return {
        'actions_by_booking': lambda b: actions_by_booking(layout, period, b),
        'attendees': attendees,
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
def delete_booking(self, request):
    request.assert_valid_csrf_token()

    if self.period.confirmed and self.state not in DELETABLE_STATES:
        show_error_on_attendee(request, self.attendee, _(
            "Only open, cancelled, denied or blocked bookings may be deleted"))

        return

    BookingCollection(request.session).delete(self)

    @request.after
    def remove_target(response):
        response.headers.add('X-IC-Remove', 'true')


@FeriennetApp.view(
    model=Booking,
    name='cancel',
    permission=Personal,
    request_method='POST')
def cancel_booking(self, request):
    request.assert_valid_csrf_token()

    if not self.period.wishlist_phase:
        if not request.is_admin:
            if self.occasion.is_past_cancellation(date.today()):
                request.alert(_(
                    "Only admins may cancel bookings at this point"
                ))

                return

    BookingCollection(request.session).cancel_booking(
        booking=self,
        score_function=self.period.scoring,
        cascade=False)

    request.success(_("The booking was cancelled successfully"))

    @request.after
    def update_matching(response):
        response.headers.add('X-IC-Trigger', 'reload-from')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'selector': '#{}'.format(self.occasion.id)
        }))


@FeriennetApp.view(
    model=Booking,
    name='toggle-star',
    permission=Personal,
    request_method='POST')
def toggle_star(self, request):

    if self.period.wishlist_phase:
        if not self.starred:
            if not self.star(max_stars=3):
                show_error_on_attendee(request, self.attendee, _(
                    "Cannot select more than three favorites per child"))
        else:
            self.unstar()
    else:
        show_error_on_attendee(request, self.attendee, _(
            "The period is not in the wishlist-phase"))

    layout = BookingCollectionLayout(self, request)
    return render_macro(layout.macros['star'], request, {'booking': self})


@FeriennetApp.view(
    model=Booking,
    name='toggle-nobble',
    permission=Secret,
    request_method='POST')
def toggle_nobble(self, request):
    if self.nobbled:
        self.unnobble()
    else:
        self.nobble()

    layout = BookingCollectionLayout(self, request)
    return render_macro(layout.macros['nobble'], request, {'booking': self})


def render_css(content, request):
    response = morepath.Response(content)
    response.content_type = 'text/css'
    return response


@FeriennetApp.view(
    model=BookingCollection,
    name='mask',
    permission=Personal,
    render=render_css)
def view_mask(self, request):
    # hackish way to get the single attendee print to work -> mask all the
    # attendees, except for the one given by param

    try:
        attendee = UUID(request.params.get('id', None)).hex
    except (ValueError, TypeError):
        return ""

    return """
        .attendee-bookings-row {
            display: none;
        }

        #attendee-%s {
            display: block;
        }
    """ % attendee


@FeriennetApp.view(
    model=Booking,
    name='invite',
    permission=Personal)
def create_invite(self, request):
    """ Creates a group_code on the booking, if one doesn't exist already
    and redirects to the GroupInvite view.

    """

    if not self.group_code:
        self.group_code = GroupInvite.create(request.session).group_code

    link = request.link(GroupInvite(request.session, self.group_code))
    return request.redirect(link)


@FeriennetApp.html(
    model=GroupInvite,
    permission=Public,
    template='invite.pt')
def view_group_invite(self, request):
    layout = GroupInviteLayout(self, request)
    occasion = self.occasion
    attendees_count = len(self.attendees)

    own_children = set(
        a.id for a in request.session.query(Attendee.id)
        .filter_by(username=request.current_username)
    )

    def may_execute_action(booking):
        return booking.attendee_id in own_children

    def group_action(booking, action):
        assert action in ('join', 'leave')

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

        url = URL(request.link(self, action))\
            .query_param('booking_id', booking.id)\
            .as_string()

        return Link(
            text=(action == 'join' and _("Join Group") or _("Leave Group")),
            url=layout.csrf_protected_url(url),
            traits=traits
        )

    return {
        'layout': layout,
        'title': _('Group for "${title}"', mapping={
            'title': occasion.activity.title
        }),
        'occasion': occasion,
        'model': self,
        'group_action': group_action,
        'wrap_occasion_link': request.return_here,
        'may_execute_action': may_execute_action,
    }


@FeriennetApp.view(
    model=GroupInvite,
    permission=Personal,
    name='join',
    request_method='POST')
def join_group(self, request):
    request.assert_valid_csrf_token()

    booking_id = request.params.get('booking_id', None)
    booking = request.session.query(Booking).filter_by(id=booking_id).first()

    if not booking:
        request.warning(_("The booking does not exist"))
        return

    own_children = set(
        a.id for a in request.session.query(Attendee.id)
        .filter_by(username=request.current_username)
    )
    if booking.attendee_id not in own_children:
        request.alert(
            _("Not permitted to join this attendee to the group"))
        return

    booking.group_code = self.group_code
    request.success(_("Successfully joined the group"))


@FeriennetApp.view(
    model=GroupInvite,
    permission=Personal,
    name='leave',
    request_method='POST')
def leave_group(self, request):
    request.assert_valid_csrf_token()

    booking_id = request.params.get('booking_id', None)
    booking = request.session.query(Booking).filter_by(id=booking_id).first()

    if not booking:
        request.warning(_("The booking does not exist"))
        return

    own_children = set(
        a.id for a in request.session.query(Attendee.id)
        .filter_by(username=request.current_username)
    )

    if booking.attendee_id not in own_children:
        request.alert(
            _("Not permitted to evict this attendee from the group"))
        return

    booking.group_code = None
    request.success(_("Successfully left the group"))
