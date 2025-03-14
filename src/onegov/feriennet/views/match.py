from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from onegov.activity import Attendee
from onegov.activity import Booking, BookingCollection, Occasion
from onegov.activity.matching import deferred_acceptance_from_database
from onegov.core.security import Secret
from onegov.core.utils import normalize_for_url
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.forms import MatchForm
from onegov.feriennet.layout import DefaultLayout, MatchCollectionLayout
from onegov.feriennet.models import PeriodMessage, GroupInvite
from onegov.core.elements import Block
from onegov.core.elements import Confirm
from onegov.core.elements import Intercooler
from onegov.core.elements import Link
from onegov.user import User, UserCollection
from sqlalchemy import and_
from sqlalchemy.orm import joinedload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.feriennet.collections.match import OccasionState
    from onegov.feriennet.request import FeriennetRequest
    from uuid import UUID
    from webob import Response


OCCASION_STATES: tuple[tuple[str, OccasionState], ...] = (
    (_('Too many attendees'), 'overfull'),
    (_('Fully occupied'), 'full'),
    (_('Enough attendees'), 'operable'),
    (_('Not enough attendees'), 'unoperable'),
    (_('No attendees'), 'empty'),
    (_('Rescinded'), 'cancelled')
)


@FeriennetApp.form(
    model=MatchCollection,
    form=MatchForm,
    template='matches.pt',
    permission=Secret)
def handle_matches(
    self: MatchCollection,
    request: FeriennetRequest,
    form: MatchForm
) -> RenderData | Response:

    layout = MatchCollectionLayout(self, request)

    if form.submitted(request):
        if not self.period.active:
            request.warning(_('Can not do matchings for an inactive period'))
            return request.redirect(request.link(self))
        elif self.period.confirmed:
            request.warning(
                _('Can not do matchings for an confirmed period'))
            return request.redirect(request.link(self))

        reset_matching(self, request)

        deferred_acceptance_from_database(
            session=request.session,
            period_id=self.period_id,
            score_function=form.scoring(request.session))

        self.period = self.period.materialize(request.session)
        self.period.scoring = form.scoring(request.session)

        if form.confirm_period:
            self.period.confirm()
            PeriodMessage.create(self.period, request, 'confirmed')
            request.success(_('The matching was confirmed successfully'))
        else:
            request.success(_('The matching run executed successfully'))

        self.session.flush()

    elif not request.POST:
        self.period = self.period.materialize(request.session)
        form.process_scoring(self.period.scoring)

    def activity_link(oid: UUID) -> str:
        return request.class_link(Occasion, {'id': oid})

    def occasion_table_link(oid: UUID) -> str:
        return request.class_link(Occasion, {'id': oid}, name='bookings-table')

    filters = {
        'states': tuple(
            Link(
                text=request.translate(text),
                active=state in self.states,
                url=request.link(self.for_filter(state=state))
            ) for text, state in OCCASION_STATES
        )
    }

    return {
        'layout': layout,
        'title': _('Matches for ${title}', mapping={
            'title': self.period.title
        }),
        'occasions': self.occasions,
        'activity_link': activity_link,
        'occasion_table_link': occasion_table_link,
        'happiness': '{}%'.format(round(self.happiness * 100)),
        'operability': '{}%'.format(round(self.operability * 100)),
        'period': self.period,
        'periods': request.app.periods,
        'form': form,
        'button_text': _('Run Matching'),
        'model': self,
        'filters': filters
    }


@FeriennetApp.html(
    model=Occasion,
    template='occasion_bookings_table.pt',
    name='bookings-table',
    permission=Secret)
def view_occasion_bookings_table(
    self: Occasion,
    request: FeriennetRequest
) -> RenderData:

    layout = DefaultLayout(self, request)

    wishlist_phase = self.period.wishlist_phase
    booking_phase = self.period.booking_phase
    phase_title = wishlist_phase and _('Wishlist') or _('Bookings')

    users: dict[str, str] = {
        username: uid.hex
        for username, uid in (
            UserCollection(request.session)
            .query().with_entities(User.username, User.id)
        )
    }

    def occasion_links(oid: UUID) -> Iterator[Link]:
        if self.period.finalized:
            yield Link(
                text=_('Signup Attendee'),
                url='#',
                traits=(
                    Block(_(
                        'The period has already been finalized. No new '
                        'attendees may be added.'
                    ), no=_('Cancel')),
                )
            )
        else:
            yield Link(
                text=_('Signup Attendee'),
                url=request.return_to(
                    request.class_link(Occasion, {'id': oid}, 'book'),
                    request.class_link(MatchCollection)
                )
            )

    @lru_cache(maxsize=10)
    def bookings_link(username: str) -> str:
        return request.class_link(
            BookingCollection, {
                'period_id': self.period.id,
                'username': username
            }
        )

    @lru_cache(maxsize=10)
    def user_link(username: str) -> str:
        return request.return_here(
            request.class_link(
                User, {'id': users[username]}
            )
        )

    @lru_cache(maxsize=10)
    def attendee_link(attendee_id: UUID) -> str:
        return request.return_here(
            request.class_link(
                Attendee, {'id': attendee_id}
            )
        )

    @lru_cache(maxsize=10)
    def group_link(group_code: str) -> str:
        return request.class_link(
            GroupInvite, {
                'group_code': group_code
            }
        )

    def booking_links(booking: Booking) -> Iterator[Link]:
        yield Link(_('User'), user_link(booking.attendee.username))
        yield Link(_('Attendee'), attendee_link(booking.attendee_id))
        yield Link(phase_title, bookings_link(booking.attendee.username))

        if booking.group_code:
            yield Link(_('Group'), group_link(booking.group_code))

        if wishlist_phase:
            yield Link(
                text=_('Remove Wish'),
                url=layout.csrf_protected_url(
                    request.class_link(Booking, {'id': booking.id})
                ),
                traits=(
                    Confirm(_(
                        "Do you really want to remove ${attendee}'s wish?",
                        mapping={
                            'attendee': booking.attendee.name
                        }
                    ), yes=_('Remove Wish'), no=_('Cancel')),
                    Intercooler(
                        request_method='DELETE',
                        target='#{}'.format(booking.id)
                    )
                )
            )

        elif booking_phase and booking.state != 'accepted':
            yield Link(
                text=_('Remove Booking'),
                url=layout.csrf_protected_url(
                    request.class_link(Booking, {'id': booking.id})
                ),
                traits=(
                    Confirm(_(
                        "Do you really want to delete ${attendee}'s booking?",
                        mapping={
                            'attendee': booking.attendee.name
                        }
                    ), yes=_('Remove Booking'), no=_('Cancel')),
                    Intercooler(
                        request_method='DELETE',
                        target='#{}'.format(booking.id)
                    )
                )
            )
        elif booking_phase and booking.state == 'accepted':
            yield Link(
                text=_('Cancel Booking'),
                url=layout.csrf_protected_url(
                    request.class_link(
                        Booking, {'id': booking.id}, 'cancel'
                    )
                ),
                traits=(
                    Confirm(
                        _(
                            "Do you really want to cancel ${attendee}'s "
                            "booking?",
                            mapping={
                                'attendee': booking.attendee.name
                            }
                        ),
                        _('This cannot be undone.'),
                        _('Cancel Booking'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                    )
                )
            )

    bookings: dict[str, list[Booking]] = {'accepted': [], 'other': []}

    q = request.session.query(Booking).filter_by(occasion_id=self.id)
    q = q.options(joinedload(Booking.attendee))

    for booking in q:
        state = booking.state == 'accepted' and 'accepted' or 'other'
        bookings[state].append(booking)

    bookings['accepted'].sort(key=lambda b: normalize_for_url(b.attendee.name))
    bookings['other'].sort(key=lambda b: normalize_for_url(b.attendee.name))

    return {
        'layout': layout,
        'bookings': bookings,
        'oid': self.id,
        'occasion_links': occasion_links,
        'booking_links': booking_links,
        'period': self.period
    }


@FeriennetApp.view(
    model=MatchCollection,
    name='reset',
    permission=Secret,
    request_method='POST')
def reset_matching(
    self: MatchCollection,
    request: FeriennetRequest,
    quiet: bool = False
) -> None:

    assert self.period.active and not self.period.confirmed

    bookings = (
        BookingCollection(request.session, self.period_id)
        .query().filter(and_(
            Booking.state != 'cancelled',
            Booking.state != 'open'
        ))
    )

    for booking in bookings:
        booking.state = 'open'
        booking.score = Decimal(0)

    if not quiet:
        request.success(_('The matching was successfully reset'))
