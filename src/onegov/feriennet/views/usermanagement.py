from __future__ import annotations

from onegov.activity import Activity, Attendee
from onegov.activity.models.invoice import BookingPeriodInvoice
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.layout import UserLayout
from onegov.user import User
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
def delete_user_group(self: User, request: FeriennetRequest) -> None:
    request.assert_valid_csrf_token()

    # Check if there are any existing activities associated with the user
    activities = request.session.query(Activity).filter_by(
        username=self.username).all()
    if activities:
        request.alert(_(
            'The user cannot be deleted because they are organizers '
            'of existing activities.'))
        return

    # Check if the user has attendees with existing bookings in the
    # current period
    attendees = request.session.query(Attendee).filter_by(
        username=self.username).all()
    bookings_to_delete = []
    if attendees and request.app.active_period:
        for attendee in attendees:
            for booking in attendee.bookings:
                bookings_to_delete.append(booking)
                if booking.occasion.period.id == request.app.active_period.id:
                    request.alert(_(
                        'The account cannot be deleted because there are '
                        'attendees with existing bookings in the current '
                        'period. Wait for the period to end or delete the '
                        'bookings first.'))
                    return

    invoices = request.session.query(BookingPeriodInvoice).filter_by(
        user_id=self.id)
    unpaid_invoices = invoices.filter(BookingPeriodInvoice.paid == False)
    if unpaid_invoices.count() > 0:
        for invoice in unpaid_invoices.all():
            if invoice.period and invoice.period.finalized:
                request.alert(_(
                    'The account cannot be deleted because there are unpaid '
                    'invoices associated with them. Mark all invoices as paid '
                    'before deleting the user.'))
                return

    # Delete all invoices
    for invoice in invoices.all():
        request.session.delete(invoice)

    # Delete all attendees
    for attendee in attendees:
        request.session.delete(attendee)

    # Delete all bookings
    for booking in bookings_to_delete:
        request.session.delete(booking)

    # Delete user
    request.session.delete(self)

    name = self.realname or self.username
    request.success(_(
        '${name} has been deleted, including all associated data.',
        mapping={
            'name': name
        }
    ))
