from __future__ import annotations

from onegov.activity import (ActivityInvoiceItem, Attendee, AttendeeCollection,
                             BookingCollection)
from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import AttendeeForm, AttendeeLimitForm
from onegov.feriennet.layout import BookingCollectionLayout
from onegov.org.elements import Link


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


@FeriennetApp.form(
    model=Attendee,
    form=AttendeeForm,
    permission=Personal,
    template='form.pt')
def edit_attendee(
    self: Attendee,
    request: FeriennetRequest,
    form: AttendeeForm
) -> RenderData | Response:

    # note: attendees are added in the views/occasion.py file
    assert request.is_admin or self.username == request.current_username

    bookings = BookingCollection(request.session)
    bookings = bookings.for_username(self.username)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return request.redirect(request.link(bookings))

    elif not request.POST:
        form.process(obj=self)

    title = _('Edit Attendee')

    layout = BookingCollectionLayout(bookings, request, self.user)
    layout.breadcrumbs.append(Link(title, request.link(self)))
    layout.edit_mode = True

    return {
        'form': form,
        'layout': layout,
        'title': title,
    }


@FeriennetApp.form(
    model=Attendee,
    form=AttendeeLimitForm,
    name='limit',
    permission=Personal,
    template='form.pt')
def edit_attendee_limit(
    self: Attendee,
    request: FeriennetRequest,
    form: AttendeeLimitForm
) -> RenderData | Response:

    assert request.is_admin or self.username == request.current_username

    bookings = BookingCollection(request.session)
    bookings = bookings.for_username(self.username)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return request.redirect(request.link(bookings))

    elif not request.POST:
        form.process(obj=self)

    title = _('Booking Limit of ${name}', mapping={
        'name': self.name
    })

    layout = BookingCollectionLayout(bookings, request, self.user)
    layout.breadcrumbs.append(Link(title, request.link(self)))
    layout.edit_mode = True

    return {
        'form': form,
        'layout': layout,
        'title': title,
    }


@FeriennetApp.view(
    model=Attendee,
    permission=Personal,
    request_method='DELETE')
def delete_attendee(
    self: Attendee,
    request: FeriennetRequest
) -> None:

    request.assert_valid_csrf_token()

    attendees = AttendeeCollection(
        request.session
    )
    deletion_possible = True
    try:
        collection = BookingCollection(request.session)
        for booking in self.bookings:
            if request.app.active_period and (
                booking.period.id == request.app.active_period.id
            ):
                deletion_possible = False
                request.alert(_(
                    'The attendee cannot be deleted because there are '
                    'existing bookings in the current period.'))
            else:
                collection.delete(booking)
        if deletion_possible:
            invoice_items = request.session.query(ActivityInvoiceItem).filter(
                ActivityInvoiceItem.attendee_id == self.id)
            for item in invoice_items:
                item.attendee_id = None
            attendees.delete(self)

            name = self.name
            request.success(_(
                '${name} and associated bookings were deleted.',
                mapping={
                    'name': name
                }
            ))
            request.redirect(request.class_link(BookingCollection))
    except Exception as e:
        if type(e).__name__ == 'IntegrityError':
            request.alert(
                _('The attendee could not be deleted because there are '
                  'existing bookings associated with it.')
            )
            request.redirect(request.link(self))
        request.alert(str(e))
