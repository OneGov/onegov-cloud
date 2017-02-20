from onegov.activity import Attendee, BookingCollection
from onegov.core.security import Personal
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import AttendeeForm
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

    layout = BookingCollectionLayout(bookings, request)
    layout.breadcrumbs.append(Link(title, request.link(self)))

    return {
        'form': form,
        'layout': layout,
        'title': title,
    }
