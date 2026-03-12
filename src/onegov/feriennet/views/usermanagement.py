from __future__ import annotations

from onegov.activity import (Activity, Attendee, Booking, BookingPeriod,
                             Occasion)
from onegov.activity.models.invoice import BookingPeriodInvoice
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import UserLayout
from onegov.user import User
from sqlalchemy.orm import joinedload
from onegov.town6.views.usermanagement import town_view_user


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.feriennet.request import FeriennetRequest
    from typing import TypeVar

    FormT = TypeVar('FormT', bound=Form)


@FeriennetApp.html(model=User, template='user.pt', permission=Secret)
def view_user(
    self: User,
    request: FeriennetRequest,
    layout: UserLayout | None = None
) -> RenderData:
    """ Shows all objects owned by the given user. """

    layout = layout or UserLayout(self, request)

    return town_view_user(
        self, request, layout)


@FeriennetApp.view(
    model=User,
    request_method='DELETE',
    permission=Secret
)
def delete_user(self: User, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    if getattr(self, 'role', None) == 'admin':
        request.alert(_('Admin accounts cannot be deleted.'))
        return

    session = request.session
    app = request.app
    active_period = getattr(app, 'active_period', None)

    # Check if there are any existing activities associated with the user
    if session.query(Activity).filter_by(username=self.username).first():
        request.alert(_(
            'The user cannot be deleted because they are organizers of '
            'existing activities.'))
        return

    # Check if the user has attendees with existing bookings in the
    # current period
    if active_period:
        booking_exists = session.query(session.query(Booking)
            .join(Attendee, Booking.attendee_id == Attendee.id)
            .join(Occasion, Booking.occasion_id == Occasion.id)
            .filter(Attendee.username == self.username,
                    Occasion.period_id == active_period.id)
            .exists()).scalar()
        if booking_exists:
            request.alert(_(
                'The account cannot be deleted because there are '
                'attendees with existing bookings in the current '
                'period. Wait for the period to end or delete the '
                'bookings first.'))
            return

    unpaid_finalized_exists = session.query(session.query(BookingPeriodInvoice)
        .join(BookingPeriodInvoice.period)
        .filter(BookingPeriodInvoice.user_id == self.id,
                BookingPeriodInvoice.paid.is_(False),
                BookingPeriod.finalized.is_(True))
        .exists()).scalar()
    if unpaid_finalized_exists:
        request.alert(_(
            'The account cannot be deleted because there are unpaid '
            'invoices associated with them. Mark all invoices as paid '
            'before deleting the user.'))
        return

    try:
        attendees = session.query(Attendee).options(
            joinedload(Attendee.bookings)
        ).filter(Attendee.username == self.username).all()

        # Delete bookings individually
        for attendee in attendees:
            for booking in attendee.bookings:
                session.delete(booking)
            session.flush()

        # Delete attendees
        for attendee in attendees:
            session.delete(attendee)

        # Delete invoices
        invoices = session.query(BookingPeriodInvoice).filter(
            BookingPeriodInvoice.user_id == self.id
        ).all()
        for invoice in invoices:
            session.delete(invoice)

        # Delete the user
        session.delete(self)

        name = self.realname or self.username
        request.success(_(
            '${name} has been deleted, including all associated data.',
            mapping={'name': name}
        ))
    except Exception:
        session.rollback()
        raise
