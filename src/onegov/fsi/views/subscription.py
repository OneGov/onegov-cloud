from __future__ import annotations

from webob import Response
from webob.exc import HTTPForbidden

from onegov.core.security import Personal, Secret, Private
from onegov.core.utils import normalize_for_url
from onegov.fsi import FsiApp
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.forms.subscription import (
    AddFsiSubscriptionForm, EditFsiSubscriptionForm,
    EditFsiPlaceholderSubscriptionForm, AddFsiPlaceholderSubscriptionForm)
from onegov.fsi.layouts.subscription import (
    SubscriptionLayout, SubscriptionCollectionLayout)
from onegov.fsi.models import CourseSubscription, CourseEvent
from onegov.fsi import _
from onegov.fsi.pdf import FsiPdf
from onegov.fsi.views.notifcations import handle_send_email


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fsi.request import FsiRequest


@FsiApp.html(
    model=SubscriptionsCollection,
    template='subscriptions.pt',
    permission=Personal
)
def view_subscriptions(
    self: SubscriptionsCollection,
    request: FsiRequest
) -> RenderData:
    layout = SubscriptionCollectionLayout(self, request)
    return {
        'layout': layout,
        'subscriptions': self.batch
    }


@FsiApp.view(
    model=SubscriptionsCollection,
    permission=Personal,
    name='pdf'
)
def attendee_list_as_pdf(
    self: SubscriptionsCollection,
    request: FsiRequest
) -> Response:

    layout = SubscriptionCollectionLayout(self, request)
    result = FsiPdf.from_subscriptions(
        self, layout, request.translate(layout.title))

    return Response(
        result.read(),
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(str(layout.title))
        )
    )


@FsiApp.form(
    model=SubscriptionsCollection,
    template='form.pt',
    name='add',
    form=AddFsiSubscriptionForm,
    permission=Private
)
def view_add_reservation(
    self: SubscriptionsCollection,
    request: FsiRequest,
    form: AddFsiSubscriptionForm
) -> RenderData | Response:

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        attendee_id = data['attendee_id']
        course_event = request.session.query(CourseEvent).filter_by(
            id=event_id).one()

        if not course_event.can_book(attendee_id):
            request.warning(
                _('There are other subscriptions for '
                  'the same course in this year'))
            return request.redirect(request.link(self))

        self.add(**data)
        request.success(_('Added a new subscription'))
        request = handle_send_email(
            course_event.reservation_template,
            request,
            (attendee_id, ),
            cc_to_sender=False,
            show_sent_count=False,
            attachments=(course_event.as_ical_attachment(), )
        )
        return request.redirect(request.link(self))

    layout = SubscriptionCollectionLayout(self, request)
    return {
        'title': _('Add Subscription'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Subscribe')
    }


@FsiApp.form(
    model=CourseSubscription,
    template='form.pt',
    name='edit',
    form=EditFsiSubscriptionForm,
    permission=Secret
)
def view_edit_reservation(
    self: CourseSubscription,
    request: FsiRequest,
    form: EditFsiSubscriptionForm
) -> RenderData | Response:

    if self.is_placeholder:
        raise HTTPForbidden()

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        coll = SubscriptionsCollection(
            request.session,
            attendee_id=data['attendee_id'],
            course_event_id=event_id,
            auth_attendee=request.attendee
        )
        res_existing = coll.query().first()
        if not res_existing:
            course_event = request.session.query(CourseEvent).filter_by(
                id=event_id).one()
            if course_event.locked and not request.is_admin:
                request.warning(
                    _("This course event can't be booked (anymore)."))
                return request.redirect(request.link(self))

            form.update_model(self)
            request.success(_('Subscription was updated'))
            request = handle_send_email(
                course_event.reservation_template,
                request,
                (data['attendee_id'],),
                cc_to_sender=False,
                show_sent_count=False,
                attachments=(course_event.as_ical_attachment(),)
            )
            return request.redirect(request.link(SubscriptionsCollection(
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

    layout = SubscriptionLayout(self, request)
    return {
        'title': _('Edit Subscription'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=CourseSubscription,
    template='form.pt',
    name='edit-placeholder',
    form=EditFsiPlaceholderSubscriptionForm,
    permission=Secret
)
def view_edit_placeholder_reservation(
    self: CourseSubscription,
    request: FsiRequest,
    form: EditFsiPlaceholderSubscriptionForm
) -> RenderData | Response:

    if not self.is_placeholder:
        raise HTTPForbidden()

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Placeholder was updated'))
        return request.redirect(request.link(SubscriptionsCollection(
            request.session,
            course_event_id=self.course_event_id,
            auth_attendee=request.attendee
        )))

    if not form.errors:
        form.apply_model(self)

    layout = SubscriptionLayout(self, request)
    return {
        'title': _('Edit Placeholder'),
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=SubscriptionsCollection,
    template='form.pt',
    name='add-placeholder',
    form=AddFsiPlaceholderSubscriptionForm,
    permission=Secret
)
def view_add_reservation_placeholder(
    self: SubscriptionsCollection,
    request: FsiRequest,
    form: AddFsiPlaceholderSubscriptionForm
) -> RenderData | Response:

    if form.submitted(request):
        data = form.get_useful_data()
        event_id = data['course_event_id']
        course_event = request.session.query(CourseEvent).filter_by(
            id=event_id).one()
        if course_event.locked and not request.is_admin:
            request.warning(
                _("This course event can't be booked (anymore)."))
            return request.redirect(request.link(self))

        default_desc = request.translate(_('Placeholder Subscription'))
        if not data.get('dummy_desc'):
            data['dummy_desc'] = default_desc

        self.add(**data)
        request.success(_('Added a new placeholder'))
        return request.redirect(request.link(self))

    layout = SubscriptionCollectionLayout(self, request)
    return {
        'title': _('Add Placeholder Subscription'),
        'model': self,
        'layout': layout,
        'form': form
    }


@FsiApp.html(
    model=SubscriptionsCollection,
    request_method='POST',
    name='add-from-course-event',
    permission=Personal
)
def view_add_from_course_event(
    self: SubscriptionsCollection,
    request: FsiRequest
) -> None:

    if self.course_event is None or self.attendee is None:
        raise HTTPForbidden()

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
    model=CourseSubscription,
    request_method='DELETE',
    permission=Secret
)
def view_delete_reservation(
    self: CourseSubscription,
    request: FsiRequest
) -> None:

    request.assert_valid_csrf_token()
    SubscriptionsCollection(
        request.session, auth_attendee=request.attendee).delete(self)
    if not self.is_placeholder and not self.course_event.is_past:
        assert self.attendee_id is not None
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
    model=CourseSubscription,
    request_method='POST',
    permission=Secret,
    name='toggle-confirm'
)
def view_toggle_confirm_reservation(
    self: CourseSubscription,
    request: FsiRequest
) -> bool:
    request.assert_valid_csrf_token()
    self.event_completed = not self.event_completed
    return self.event_completed
