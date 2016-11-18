from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.security import Private, Personal, Public
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms import AttendeeForm, OccasionForm
from onegov.feriennet.layout import OccasionFormLayout
from onegov.feriennet.models import VacationActivity


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
            start=form.start.data,
            end=form.end.data,
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
        'form': form
    }


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='DELETE')
def delete_occasion(self, request):
    request.assert_valid_csrf_token()

    OccasionCollection(request.app.session()).delete(self)


@FeriennetApp.form(
    model=Occasion,
    form=AttendeeForm,
    permission=Personal,
    name='anmelden',
    template='enroll_form.pt')
def book_occasion(self, request, form):

    # pass the form model for extended validation if data was posted
    form.model = request.POST and self or None

    if form.submitted(request):
        attendees = AttendeeCollection(request.app.session())
        user = request.current_user

        if form.is_new:
            attendee = attendees.add(
                user=user,
                name=form.name.data,
                birth_date=form.birth_date.data
            )
        else:
            attendee = attendees.by_id(form.attendee.data)

        bookings = BookingCollection(request.app.session())
        bookings.add(
            user=user,
            attendee=attendee,
            occasion=self
        )

        request.success(
            _("The occasion was added to ${name}'s wishlist", mapping={
                'name': attendee.name
            }))

        return request.redirect(request.link(self.activity))

    title = _("Enroll Attendee")

    return {
        'layout': OccasionFormLayout(self.activity, request, title),
        'title': title,
        'form': form,
        'occasion': self
    }
