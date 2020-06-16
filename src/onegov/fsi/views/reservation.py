from webob import Response

from onegov.core.security import Personal, Secret, Private
from onegov.core.utils import normalize_for_url
from onegov.fsi import FsiApp
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.forms.reservation import AddFsiReservationForm, \
    EditFsiReservationForm, EditFsiPlaceholderReservationForm, \
    AddFsiPlaceholderReservationForm
from onegov.fsi.layouts.reservation import ReservationLayout, \
    ReservationCollectionLayout
from onegov.fsi.models import CourseReservation, CourseEvent
from onegov.fsi import _
from onegov.fsi.pdf import FsiPdf
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


@FsiApp.view(
    model=ReservationCollection,
    permission=Personal,
    name='pdf'
)
def attendee_list_as_pdf(self, request):
    layout = ReservationCollectionLayout(self, request)
    result = FsiPdf.from_subscriptions(
        self, layout, request.translate(layout.title))

    return Response(
        result.read(),
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(f"{layout.title}")
        )
    )


@FsiApp.form(
    model=ReservationCollection,
    template='form.pt',
    name='add',
    form=AddFsiReservationForm,
    permission=Private
)
def view_add_reservation(self, request, form):
    layout = ReservationCollectionLayout(self, request)

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        attendee_id = data['attendee_id']
        course_event = request.session.query(CourseEvent).filter_by(
            id=event_id).first()

        if not course_event.can_book(attendee_id):
            request.warning(
                _("There are other subscriptions for "
                  "the same course in this year"))
            return request.redirect(request.link(self))

        self.add(**data)
        request.success(_("Added a new subscription"))
        request = handle_send_email(
            course_event.reservation_template,
            request,
            (attendee_id, ),
            cc_to_sender=False,
            show_sent_count=False,
            attachments=(course_event.as_ical_attachment(), )
        )
        return request.redirect(request.link(self))

    return {
        'title': _('Add Subscription'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Subscribe')
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
    assert not self.is_placeholder

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        coll = ReservationCollection(
            request.session,
            attendee_id=data['attendee_id'],
            course_event_id=event_id,
            auth_attendee=request.attendee
        )
        res_existing = coll.query().first()
        if not res_existing:
            course_event = request.session.query(CourseEvent).filter_by(
                id=event_id).first()
            if course_event.locked and not request.is_admin:
                request.warning(
                    _("This course event can't be booked (anymore)."))
                return request.redirect(request.link(self))

            form.update_model(self)
            request.success(_("Subscription was updated"))
            request = handle_send_email(
                course_event.reservation_template,
                request,
                (data['attendee_id'],),
                cc_to_sender=False,
                show_sent_count=False,
                attachments=(course_event.as_ical_attachment(),)
            )
            return request.redirect(request.link(ReservationCollection(
                request.session,
                auth_attendee=request.attendee,
                course_event_id=self.course_event_id,
                attendee_id=self.attendee_id
            )))
        else:
            request.warning(_('Subscription already exists'))
            return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'title': _('Edit Subscription'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=CourseReservation,
    template='form.pt',
    name='edit-placeholder',
    form=EditFsiPlaceholderReservationForm,
    permission=Secret
)
def view_edit_placeholder_reservation(self, request, form):
    layout = ReservationLayout(self, request)
    assert self.is_placeholder

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Placeholder was updated"))
        return request.redirect(request.link(ReservationCollection(
            request.session,
            course_event_id=self.course_event_id,
            auth_attendee=request.attendee
        )))

    if not form.errors:
        form.apply_model(self)

    return {
        'title': _('Edit Placeholder'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=ReservationCollection,
    template='form.pt',
    name='add-placeholder',
    form=AddFsiPlaceholderReservationForm,
    permission=Secret
)
def view_add_reservation_placeholder(self, request, form):
    layout = ReservationCollectionLayout(self, request)

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        course_event = request.session.query(CourseEvent).filter_by(
            id=event_id).first()
        if course_event.locked and not request.is_admin:
            request.warning(
                _("This course event can't be booked (anymore)."))
            return request.redirect(request.link(self))

        default_desc = request.translate(_('Placeholder Reservation'))
        if not data.get('dummy_desc'):
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
        show_sent_count=False,
        attachments=(self.course_event.as_ical_attachment(),)
    )
    request.success(_('New subscription successfully added'))


@FsiApp.html(
    model=CourseReservation,
    request_method='DELETE',
    permission=Secret
)
def view_delete_reservation(self, request):
    request.assert_valid_csrf_token()
    ReservationCollection(
        request.session, auth_attendee=request.attendee).delete(self)
    if not self.is_placeholder:
        request = handle_send_email(
            self.course_event.cancellation_template,
            request,
            (self.attendee_id, ),
            cc_to_sender=False,
            show_sent_count=True
        )
        request.success(_('Subscription successfully deleted'))
    else:
        request.success(_('Placeholder successfully deleted'))


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
