from onegov.activity import AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.security import Private, Personal, Public
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms import AttendeeSignupForm, OccasionForm
from onegov.feriennet.layout import OccasionFormLayout
from onegov.feriennet.models import VacationActivity
from onegov.user import User, UserCollection


@FeriennetApp.view(
    model=Occasion,
    permission=Public,
)
def view_occasion(self, request):
    return request.redirect(request.link(self.activity))


@FeriennetApp.form(
    model=VacationActivity,
    template='form.pt',
    form=OccasionForm,
    permission=Private,
    name='neue-durchfuehrung')
def new_occasion(self, request, form):

    if form.submitted(request):
        occasions = OccasionCollection(request.app.session())
        periods = PeriodCollection(request.app.session())

        form.populate_obj(occasions.add(
            activity=self,
            start=form.parsed_dates[0].start,
            end=form.parsed_dates[0].end,
            timezone=form.timezone,
            period=periods.by_id(form.period_id.data)
        ))

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    return {
        'layout': OccasionFormLayout(self, request, _("New Occasion")),
        'title': _("New Occasion"),
        'form': form
    }


@FeriennetApp.form(
    model=Occasion,
    template='form.pt',
    form=OccasionForm,
    permission=Private,
    name='duplizieren')
def clone_occasion(self, request, form):

    if form.submitted(request):
        occasions = OccasionCollection(request.app.session())
        periods = PeriodCollection(request.app.session())

        form.populate_obj(occasions.add(
            activity=self.activity,
            start=form.parsed_dates[0].start,
            end=form.parsed_dates[0].end,
            timezone=form.timezone,
            period=periods.by_id(form.period_id.data)
        ))

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.activity))
    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': OccasionFormLayout(
            self.activity, request, _("Clone Occasion")),
        'title': _("Clone Occasion"),
        'form': form
    }


@FeriennetApp.form(
    model=Occasion,
    template='form.pt',
    form=OccasionForm,
    permission=Private,
    name='bearbeiten')
def edit_occasion(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.activity))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': OccasionFormLayout(
            self.activity, request, _("Edit Occasion")),
        'title': _("Edit Occasion"),
        'form': form,
    }


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='DELETE')
def delete_occasion(self, request):
    request.assert_valid_csrf_token()

    OccasionCollection(request.app.session()).delete(self)


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='POST',
    name='cancel')
def cancel_occasion(self, request):
    request.assert_valid_csrf_token()

    self.cancel()


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='POST',
    name='reinstate')
def reinstate_occasion(self, request):
    request.assert_valid_csrf_token()

    self.cancelled = False


@FeriennetApp.form(
    model=Occasion,
    form=AttendeeSignupForm,
    permission=Personal,
    name='anmelden',
    template='enroll_form.pt')
def book_occasion(self, request, form):

    if form.submitted(request):
        attendees = AttendeeCollection(request.app.session())
        user = form.user

        if form.is_new:
            attendee = attendees.add(
                user=user,
                name=form.name,
                birth_date=form.birth_date.data,
                gender=form.gender.data,
                notes=form.notes.data
            )
        else:
            attendee = attendees.by_id(form.attendee.data)
            assert attendee.username == form.username

        # should be caught by the form
        assert not (self.full and self.period.confirmed)
        assert self.activity.state == 'accepted'

        bookings = BookingCollection(request.app.session())

        # if there's a cancelled booking blocking the way, reactivate it
        booking = None

        if not form.is_new:
            o = OccasionCollection(request.app.session()).query()
            o = o.with_entities(Occasion.id)
            o = o.filter(Occasion.activity_id == self.activity_id)
            o = o.filter(Occasion.period_id == self.period_id)

            q = bookings.query()
            q = q.filter(Booking.username == user.username)
            q = q.filter(Booking.attendee == attendee)
            q = q.filter(Booking.occasion_id.in_(o.subquery()))
            q = q.filter(Booking.state == 'cancelled')

            # somewhat unnecessary, but let's be extra sure
            q = q.filter(Booking.period_id == self.period_id)

            booking = q.first()

            if booking:
                booking.state = 'open'
                booking.occasion_id = self.id

        if booking is None:
            booking = bookings.add(
                user=user,
                attendee=attendee,
                occasion=self
            )

        if self.period.confirmed:
            bookings.accept_booking(booking)
            request.success(
                _("The booking for ${name} was succesfull", mapping={
                    'name': attendee.name
                })
            )
        else:
            request.success(
                _("The occasion was added to ${name}'s wishlist", mapping={
                    'name': attendee.name
                }))

        return request.redirect(request.link(self.activity))

    title = _("Enroll Attendee")

    users = []

    if request.is_admin:
        u = UserCollection(request.app.session()).query()
        u = u.with_entities(User.username, User.title)
        u = u.order_by(User.title)

        users = u

    return {
        'layout': OccasionFormLayout(self.activity, request, title),
        'title': title,
        'form': form,
        'occasion': self,
        'users': users,
        'button_text': _("Enroll")
    }
