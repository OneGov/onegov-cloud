from __future__ import annotations

from onegov.core.security import Personal, Secret
from onegov.core.templates import render_macro
from onegov.fsi import FsiApp
from onegov.fsi.collections.course_event import (
    CourseEventCollection, PastCourseEventCollection)
from onegov.fsi.forms.course_event import CourseEventForm
from onegov.fsi import _
from onegov.fsi.layouts.course_event import (
    EditCourseEventLayout, DuplicateCourseEventLayout, AddCourseEventLayout,
    CourseEventCollectionLayout, CourseEventLayout)
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.views.notifcations import handle_send_email


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fsi.request import FsiRequest
    from webob import Response


@FsiApp.html(
    model=CourseEventCollection,
    template='course_events.pt',
    permission=Personal
)
def view_course_event_collection(
    self: CourseEventCollection,
    request: FsiRequest
) -> RenderData:

    layout = CourseEventCollectionLayout(self, request)
    has_events = request.session.query(self.query().exists()).scalar()
    return {
        'layout': layout,
        'model': self,
        'events': self.query() if has_events else None
    }


@FsiApp.view(
    model=CourseEventCollection,
    permission=Personal,
    name='as-listing'
)
def view_course_event_collection_json(
    self: CourseEventCollection,
    request: FsiRequest
) -> str:

    layout = CourseEventCollectionLayout(self, request)
    has_events = request.session.query(self.query().exists()).scalar()
    return render_macro(
        layout.macros['course_event_listing'],
        request,
        {
            'events': self.query() if has_events else None,
            'layout': layout
        }
    )


@FsiApp.html(
    model=PastCourseEventCollection,
    template='past_course_events.pt',
    permission=Personal,
)
def view_past_course_event_collection(
    self: PastCourseEventCollection,
    request: FsiRequest
) -> RenderData:
    layout = CourseEventCollectionLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'events': self.batch,
    }


@FsiApp.form(
    model=CourseEventCollection,
    template='form.pt',
    name='add',
    form=CourseEventForm,
    permission=Secret
)
def view_add_course_event(
    self: CourseEventCollection,
    request: FsiRequest,
    form: CourseEventForm
) -> RenderData | Response:

    if form.submitted(request):
        course_event = self.add(**form.get_useful_data())
        request.success(_('Added a new course event'))
        return request.redirect(request.link(course_event))

    layout = AddCourseEventLayout(self, request)
    layout.edit_mode = True
    return {
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.html(
    model=CourseEvent,
    template='course_event.pt',
    permission=Personal
)
def view_course_event(
    self: CourseEvent,
    request: FsiRequest
) -> RenderData:

    layout = CourseEventLayout(self, request)
    return {
        'layout': layout,
        'model': self,
    }


@FsiApp.form(
    model=CourseEvent,
    template='form.pt',
    name='edit',
    form=CourseEventForm,
    permission=Secret
)
def view_edit_course_event(
    self: CourseEvent,
    request: FsiRequest,
    form: CourseEventForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model(self)

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = EditCourseEventLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=CourseEvent,
    template='form.pt',
    name='duplicate',
    form=CourseEventForm,
    permission=Secret
)
def view_duplicate_course_event(
    self: CourseEvent,
    request: FsiRequest,
    form: CourseEventForm
) -> RenderData | Response:

    if form.submitted(request):
        duplicate = CourseEventCollection(
            request.session).add(**form.get_useful_data())

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(duplicate))

    form.apply_model(self.duplicate)

    layout = DuplicateCourseEventLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.view(
    model=CourseEvent,
    request_method='DELETE',
    permission=Secret
)
def delete_course_event(self: CourseEvent, request: FsiRequest) -> None:
    request.assert_valid_csrf_token()
    if not self.subscriptions.first():
        CourseEventCollection(request.session).delete(self)
    else:
        request.warning(_(
            'This event has registrations and can not be deleted'))


@FsiApp.view(
    model=CourseEvent,
    request_method='POST',
    permission=Secret,
    name='cancel'
)
def cancel_course_event(self: CourseEvent, request: FsiRequest) -> None:
    request.assert_valid_csrf_token()
    self.status = 'canceled'

    recipients = [a.id for a in self.attendees]

    if recipients:
        request = handle_send_email(
            self.cancellation_template,
            request,
            recipients,
            cc_to_sender=True,
            show_sent_count=True
        )
    else:
        request.warning(_('No recipients and no cancellation emails sent'))
