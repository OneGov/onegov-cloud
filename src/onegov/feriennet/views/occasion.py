from datetime import date
from onegov.activity import AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import InvoiceCollection
from onegov.activity import Occasion, OccasionCollection, OccasionNeed
from onegov.activity import PeriodCollection
from onegov.core.security import Private, Personal, Public
from onegov.core.templates import render_template
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections.billing import BookingInvoiceBridge
from onegov.feriennet.forms import AttendeeSignupForm
from onegov.feriennet.forms import OccasionForm
from onegov.feriennet.forms import OccasionNeedForm
from onegov.feriennet.layout import OccasionFormLayout
from onegov.feriennet.models import VacationActivity
from onegov.org.layout import DefaultMailLayout
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
        form.dates.data = form.dates_to_json(dates=None)

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
            "this occasion."
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
        WHERE activity_id = :activity_id \
          AND "order" <= :order \
          AND "period_id" = :period_id
    """, {
        'activity_id': self.activity_id,
        'order': self.order,
        'period_id': self.period.id
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
                notes=form.notes.data,
                differing_address=form.differing_address.data,
                address=form.address.data
                if form.differing_address.data else None,
                zip_code=form.zip_code.data
                if form.differing_address.data else None,
                place=form.place.data if form.differing_address.data else None,
                political_municipality=form.political_municipality.data if
                form.political_municipality and form.differing_address.data
                else None
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

        # apply the group code, if given
        if form.group_code.data:
            booking.group_code = form.group_code.data

        # if the TOS have been accepted, record this now
        if hasattr(form, 'accept_tos') and form.accept_tos:
            if form.accept_tos.data:
                request.current_user.data['tos_accepted'] = True

        # to get the final cost, we need to accept bookings without wishlist
        if self.period.confirmed:
            bookings.accept_booking(booking)

        # if the period has been finalized, an admin is responsible and we
        # need to create an invoice item that goes with the booking
        if self.period.finalized:
            assert request.is_admin or self.period.book_finalized

            bridge = BookingInvoiceBridge(request.session, self.period)
            bridge.process(booking)
            bridge.complete(
                all_inclusive_booking_text=request.translate(_("Passport")))

        if self.period.confirmed:
            request.success(
                _("The booking for ${name} was succesfull", mapping={
                    'name': attendee.name
                })
            )

            bookings_link = '<a href="{}">{}</a>'.format(
                request.class_link(BookingCollection, {
                    'period_id': self.period.id
                }),
                request.translate(_("Bookings"))
            )

            subject = request.translate(
                _('Booking of ${attendee} for "${title}"',
                    mapping={
                        'title': self.activity.title,
                        'attendee': attendee.name
                    }))
            if self.period.booking_start <= date.today():
                request.app.send_transactional_email(
                    subject=subject,
                    receivers=(user.username, ),
                    content=render_template(
                        'mail_booking_accepted.pt', request, {
                            'layout': DefaultMailLayout(self, request),
                            'title': subject,
                            'model': self,
                            'bookings_link': bookings_link,
                            'name': attendee.name,
                            'dates': self.dates
                        }
                    )
                )
        else:
            request.success(
                _("The occasion was added to ${name}'s wishlist", mapping={
                    'name': attendee.name
                }))

        if self.period.finalized:
            return request.redirect(request.class_link(InvoiceCollection))
        else:
            return request.redirect(request.link(self.activity))

    # pre select the attendee if given
    if 'attendee_id' in request.params:
        form.attendee.data = request.params['attendee_id'].replace('-', '')
        form.group_code.data = request.params.get('group_code')

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
            number=form.number,
            accept_signups=form.accept_signups.data,
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

        # XXX the observer only works when we add/remove things from the list,
        # not when we change something inside the list
        self.occasion.observe_needs(self.occasion.needs)

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

    # Likewise, before flushing the changes, the needs observer is not
    # triggered by an event.
    occasion = self.occasion
    request.session.delete(self)
    occasion.observe_needs(occasion.needs)
