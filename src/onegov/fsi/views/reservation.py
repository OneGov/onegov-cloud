from onegov.core.security import Personal, Secret
from onegov.fsi import FsiApp
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.forms.reservation import AddFsiReservationForm, \
    EditFsiReservationForm
from onegov.fsi.layouts.reservation import ReservationLayout, \
    ReservationCollectionLayout
from onegov.fsi.models import CourseReservation
from onegov.fsi import _
from onegov.fsi.views.notifcations import handle_send_email


@FsiApp.html(
    model=ReservationCollection,
    template='reservations.pt',
    permission=Personal
)
def view_reservations(self, request):
    layout = ReservationCollectionLayout(self, request)
    return {
        'layout': layout,
        'reservations': self.batch
    }


@FsiApp.form(
    model=ReservationCollection,
    template='form.pt',
    name='add',
    form=AddFsiReservationForm,
    permission=Secret
)
def view_add_reservation(self, request, form):
    layout = ReservationCollectionLayout(self, request)

    if form.submitted(request):
        self.add(**form.get_useful_data())
        request.success(_("Added a new reservation"))
        return request.redirect(request.link(self))

    return {
        'title': _('Add Reservation'),
        'model': self,
        'layout': layout,
        'form': form
    }


@FsiApp.form(
    model=CourseReservation,
    template='form.pt',
    name='edit',
    form=EditFsiReservationForm,
    permission=Secret
)
def view_edit_reservation(self, request, form):
    layout = ReservationLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Reservation was updated"))
        return request.redirect(request.link(ReservationCollection(
            request.session,
            course_event_id=self.id,
            attendee_id=self.attendee_id
        )))
    title = _('Edit Placeholder') if self.is_placeholder \
        else _('Edit Reservation')

    if not form.errors:
        form.apply_model(self)

    return {
        'title': title,
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=ReservationCollection,
    template='form.pt',
    name='add-placeholder',
    form=AddFsiReservationForm,
    permission=Secret
)
def view_add_reservation_placeholder(self, request, form):
    layout = ReservationCollectionLayout(self, request)

    if form.submitted(request):
        data = form.get_useful_data()
        default_desc = request.translate(_('Placeholder Reservation'))
        desc = data.setdefault('dummy_desc', default_desc)
        if not desc:
            data['dummy_desc'] = default_desc
        self.add(**data)
        request.success(_("Added a new placeholder"))
        return request.redirect(request.link(self))

    return {
        'title': _('Add Placeholder Reservation'),
        'model': self,
        'layout': layout,
        'form': form
    }


@FsiApp.html(
    model=ReservationCollection,
    request_method='POST',
    name='add-from-course-event',
    permission=Personal
)
def view_add_from_course_event(self, request):
    request.assert_valid_csrf_token()
    self.add(
        attendee_id=self.attendee_id,
        course_event_id=self.course_event_id)
    request = handle_send_email(
        self.course_event.reservation_template,
        request,
        (self.attendee, ),
        cc_to_sender=False,
        show_sent_count=False
    )
    request.success(_('New subscription successfully added'))


@FsiApp.html(
    model=CourseReservation,
    request_method='DELETE',
    permission=Secret
)
def view_delete_reservation(self, request):
    request.assert_valid_csrf_token()
    ReservationCollection(request.session).delete(self)
    request.success(_('Subscription successfully deleted'))


@FsiApp.json(
    model=CourseReservation,
    request_method='POST',
    permission=Secret,
    name='toggle-confirm'
)
def view_toggle_confirm_reservation(self, request):
    request.assert_valid_csrf_token()
    self.event_completed = not self.event_completed
    return self.event_completed
