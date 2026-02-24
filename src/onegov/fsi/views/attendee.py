from __future__ import annotations

from onegov.core.security import Private, Personal, Secret
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi import _
from onegov.fsi.forms.course_attendee import (
    CourseAttendeeForm, AddExternalAttendeeForm)
from onegov.fsi.layouts.course_attendee import (
    CourseAttendeeLayout, CourseAttendeeCollectionLayout)
from onegov.fsi.models import CourseAttendee, CourseEvent


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fsi.models import CourseSubscription
    from onegov.fsi.request import FsiRequest
    from sqlalchemy.orm import Query
    from webob import Response


@FsiApp.html(
    model=CourseAttendeeCollection,
    template='course_attendees.pt',
    permission=Private
)
def view_course_attendee_collection(
    self: CourseAttendeeCollection,
    request: FsiRequest
) -> RenderData:

    layout = CourseAttendeeCollectionLayout(self, request)
    has_entries = request.session.query(self.query().exists()).scalar()
    return {
        'title': layout.title,
        'has_entries': has_entries,
        'layout': layout,
        'model': self
    }


@FsiApp.html(
    model=CourseAttendee,
    template='course_attendee.pt',
    permission=Personal
)
def view_course_attendee(
    self: CourseAttendee,
    request: FsiRequest
) -> RenderData:

    layout = CourseAttendeeLayout(self, request)
    limit = 5

    def last_subscriptions(
        query: Query[CourseSubscription],
        limit: int
    ) -> list[CourseSubscription]:
        return (
            query.join(CourseEvent)
            .order_by(CourseEvent.start.desc())
            .limit(limit).all()
        )

    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'limit': limit,
        'last_subscriptions': last_subscriptions(self.subscriptions, limit)
    }


@FsiApp.form(
    model=CourseAttendee,
    name='edit',
    form=CourseAttendeeForm,
    template='form.pt',
    permission=Secret
)
def view_edit_course_attendee(
    self: CourseAttendee,
    request: FsiRequest,
    form: CourseAttendeeForm
) -> RenderData | Response:

    if form.submitted(request):

        form.update_model(self)

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = CourseAttendeeLayout(self, request)
    return {
        'title': layout.title,
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.form(
    model=CourseAttendeeCollection,
    template='form.pt',
    form=AddExternalAttendeeForm,
    name='add-external',
    permission=Private
)
def view_add_external_attendee(
    self: CourseAttendeeCollection,
    request: FsiRequest,
    form: AddExternalAttendeeForm
) -> RenderData | Response:

    if form.submitted(request):
        attendee = self.add(**form.get_useful_data())
        request.success(_('Added a new external attendee'))
        return request.redirect(request.link(attendee))

    layout = CourseAttendeeCollectionLayout(self, request)
    layout.edit_mode = True
    return {
        'title': layout.title,
        'layout': layout,
        'form': form
    }


@FsiApp.html(
    model=CourseAttendee,
    request_method='DELETE',
    permission=Secret
)
def view_delete_reservation(
    self: CourseAttendee,
    request: FsiRequest
) -> None:

    request.assert_valid_csrf_token()
    if self.is_external:
        CourseAttendeeCollection(
            request.session,
            auth_attendee=request.attendee).delete(self)
        request.success(_('External attendee successfully deleted'))
    else:
        request.warning(_('Can only delete external attendees'))
