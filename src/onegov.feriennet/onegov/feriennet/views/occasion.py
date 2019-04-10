from onegov.activity import AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection, OccasionNeed
from onegov.activity import PeriodCollection
from onegov.core.security import Private, Personal, Public
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms import AttendeeSignupForm
from onegov.feriennet.forms import OccasionForm
from onegov.feriennet.forms import OccasionNeedForm
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
    name='new-occasion')
def new_occasion(self, request, form):

    if form.submitted(request):
        occasions = OccasionCollection(request.session)
        periods = PeriodCollection(request.session)

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
    name='clone')
def clone_occasion(self, request, form):

    if form.submitted(request):
        occasions = OccasionCollection(request.session)
        periods = PeriodCollection(request.session)

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
    name='edit')
def edit_occasion(self, request, form):

    if self.period.confirmed:
        warning = _(
            "The period of this occasion has already been confirmed. "
            "It is not recommended to change the period associated with "
            "this occasion. "
        )
    else:
        warning = None

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
        'callout': warning
    }


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='DELETE')
def delete_occasion(self, request):
    request.assert_valid_csrf_token()

    OccasionCollection(request.session).delete(self)


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
    name='book',
    template='enroll_form.pt')
def book_occasion(self, request, form):

    # for the "nth. occasion" title
    number = request.session.execute("""
        SELECT count(*) FROM occasions
        WHERE activity_id = :activity_id AND "order" <= :order
    """, {
        'activity_id': self.activity_id,
        'order': self.order
    }).scalar()

    if form.submitted(request):
        attendees = AttendeeCollection(request.session)
        user = form.user

        if form.is_new_attendee:
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

        bookings = BookingCollection(request.session)

        # if there's a canceled/denied booking blocking the way, reactivate it
        booking = None

        if not form.is_new_attendee:
            booking = bookings.query()\
                .filter(Booking.occasion_id == self.id)\
                .filter(Booking.username == user.username)\
                .filter(Booking.attendee == attendee)\
                .filter(Booking.state.in_((
                    'cancelled',
                    'denied',
                    'blocked',
                )))\
                .first()

            if booking:
                booking.state = 'open'

        if booking is None:
            booking = bookings.add(
                user=user,
                attendee=attendee,
                occasion=self
            )

        # if the TOS have been accepted, record this now
        if hasattr(form, 'accept_tos') and form.accept_tos:
            if form.accept_tos.data:
                request.current_user.data['tos_accepted'] = True

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
        u = UserCollection(request.session).query()
        u = u.with_entities(User.username, User.title)
        u = u.order_by(User.title)

        users = u

    return {
        'layout': OccasionFormLayout(self.activity, request, title),
        'title': title,
        'form': form,
        'occasion': self,
        'users': users,
        'button_text': _("Enroll"),
        'number': number,
    }


@FeriennetApp.form(
    model=Occasion,
    permission=Private,
    form=OccasionNeedForm,
    template='form.pt',
    name='add-need')
def handle_new_occasion_need(self, request, form):

    if form.submitted(request):
        self.needs.append(OccasionNeed(
            occasion_id=self.id,
            name=form.name.data,
            description=form.description.data,
            number=form.number
        ))

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    return {
        'layout': OccasionFormLayout(
            self.activity, request, _("New need")),
        'title': _("New need"),
        'form': form
    }


@FeriennetApp.form(
    model=OccasionNeed,
    permission=Private,
    form=OccasionNeedForm,
    template='form.pt',
    name='edit')
def handle_occasion_need(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.occasion))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': OccasionFormLayout(
            self.occasion.activity, request, _("Edit need")),
        'title': self.name,
        'form': form
    }


@FeriennetApp.view(
    model=OccasionNeed,
    permission=Private,
    request_method='DELETE')
def delete_occasion_need(self, request):
    request.assert_valid_csrf_token()
    request.session.delete(self)
