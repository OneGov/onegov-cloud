from onegov.activity import Attendee, BookingCollection
from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import AttendeeForm, AttendeeLimitForm
from onegov.feriennet.layout import BookingCollectionLayout
from onegov.org.elements import Link


@FeriennetApp.form(
    model=Attendee,
    form=AttendeeForm,
    permission=Personal,
    template='form.pt')
def edit_attendee(self, request, form):
    # note: attendees are added in the views/occasion.py file
    assert request.is_admin or self.username == request.current_username

    bookings = BookingCollection(request.app.session())
    bookings = bookings.for_username(self.username)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return request.redirect(request.link(bookings))

    elif not request.POST:
        form.process(obj=self)

    title = _("Edit Attendee")

    layout = BookingCollectionLayout(bookings, request, self.user)
    layout.breadcrumbs.append(Link(title, request.link(self)))

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
def edit_attendee_limit(self, request, form):
    assert request.is_admin or self.username == request.current_username

    bookings = BookingCollection(request.app.session())
    bookings = bookings.for_username(self.username)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return request.redirect(request.link(bookings))

    elif not request.POST:
        form.process(obj=self)

    title = _("Booking Limit of ${name}", mapping={
        'name': self.name
    })

    layout = BookingCollectionLayout(bookings, request, self.user)
    layout.breadcrumbs.append(Link(title, request.link(self)))

    return {
        'form': form,
        'layout': layout,
        'title': title,
    }
