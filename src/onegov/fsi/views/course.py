from __future__ import annotations

from onegov.core.security import Private, Secret, Personal
from onegov.core.templates import render_template
from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.forms.course import CourseForm, InviteCourseForm
from onegov.fsi import _
from onegov.fsi.layouts.course import (
    CourseCollectionLayout, CourseLayout, AddCourseLayout, EditCourseLayout,
    InviteCourseLayout, CourseInviteMailLayout)
from onegov.fsi.models import CourseAttendee

from onegov.fsi.models.course import Course
from onegov.fsi.models.course_notification_template import (
    CourseInvitationTemplate, CourseNotificationTemplate)
from onegov.user import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from onegov.core.types import EmailJsonDict, RenderData
    from onegov.fsi.request import FsiRequest
    from webob import Response


def handle_send_invitation_email(
    self: CourseInvitationTemplate,
    course: Course,
    request: FsiRequest,
    recipients: Collection[str],
    cc_to_sender: bool = True
) -> FsiRequest:
    """Recipients must be a list of emails"""

    if not recipients:
        request.alert(_('There are no recipients matching the selection'))
        return request

    att = request.attendee
    assert att is not None
    if cc_to_sender and att.email not in recipients:
        recipients = list(recipients)
        recipients.append(att.email)

    mail_layout = CourseInviteMailLayout(course, request)

    errors = []

    def email_iter() -> Iterator[EmailJsonDict]:
        for email in recipients:

            attendee = request.session.query(
                CourseAttendee).filter_by(_email=email).first()
            if not attendee:
                user = request.session.query(User).filter_by(
                    username=email).first()
                if not user:
                    errors.append(email)
                    continue
                attendee = user.attendee  # type:ignore[attr-defined]
                if not attendee:
                    # This is a case that should not happen except in testing
                    errors.append(email)
                    continue

            content = render_template('mail_notification.pt', request, {
                'layout': mail_layout,
                'title': self.subject,
                'notification': self.text_html,
                'attendee': attendee,
            })

            yield request.app.prepare_email(
                category='transactional',
                receivers=(attendee.email,),
                subject=self.subject,
                content=content,
            )

    request.app.send_transactional_email_batch(email_iter())

    request.success(_(
        'Successfully sent the e-mail to ${count} recipients',
        mapping={
            'count': len(recipients) - len(errors)
        }
    ))

    if errors:
        request.warning(
            _('Following emails were unknown: ${mail_list}',
              mapping={'mail_list': ', '.join(errors)})
        )
    return request


@FsiApp.html(
    model=Course,
    template='mail_notification.pt',
    permission=Private,
    name='embed'
)
def view_email_preview_for_course(
    self: Course,
    request: FsiRequest
) -> RenderData:

    mail_layout = CourseInviteMailLayout(self, request)

    template = CourseNotificationTemplate()

    return {
        'layout': mail_layout,
        'title': template.subject,
        'notification': template.text_html,
        'attendee': request.attendee
    }


@FsiApp.html(
    model=CourseCollection,
    template='courses.pt',
    permission=Personal
)
def view_course_collection(
    self: CourseCollection,
    request: FsiRequest
) -> RenderData:
    layout = CourseCollectionLayout(self, request)
    return {
        'layout': layout,
        'model': self,
    }


@FsiApp.form(
    model=CourseCollection,
    template='form.pt',
    name='add',
    form=CourseForm,
    permission=Secret
)
def view_add_course_event(
    self: CourseCollection,
    request: FsiRequest,
    form: CourseForm
) -> RenderData | Response:

    if form.submitted(request):
        course = self.add(**form.get_useful_data())
        request.success(_('Added a new course'))
        return request.redirect(request.link(course))

    layout = AddCourseLayout(self, request)
    layout.include_editor()
    layout.edit_mode = True
    return {
        'layout': layout,
        'model': self,
        'form': form
    }


@FsiApp.html(
    model=Course,
    template='course.pt',
    permission=Personal
)
def view_course_event(self: Course, request: FsiRequest) -> RenderData:
    layout = CourseLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'events': self.future_events.all()
    }


@FsiApp.json(
    model=Course,
    permission=Personal,
    name='content-json'
)
def get_course_event_content(self: Course, request: FsiRequest) -> str:
    return self.description_html


@FsiApp.form(
    model=Course,
    template='form.pt',
    name='edit',
    form=CourseForm,
    permission=Secret
)
def view_edit_course_event(
    self: Course,
    request: FsiRequest,
    form: CourseForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model(self)

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    layout = EditCourseLayout(self, request)
    layout.include_editor()

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=Course,
    template='course_invite.pt',
    form=InviteCourseForm,
    name='invite',
    permission=Private
)
def invite_attendees_for_event(
    self: Course,
    request: FsiRequest,
    form: InviteCourseForm
) -> RenderData | Response:

    if form.submitted(request):
        recipients = form.get_useful_data()
        request = handle_send_invitation_email(
            CourseInvitationTemplate(),
            self,
            request,
            recipients,
            cc_to_sender=False
        )
        return request.redirect(request.link(self))

    layout = InviteCourseLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form,
        'button_text': _('Send Invitation'),
        'email': CourseInvitationTemplate(),
        'iframe_link': request.link(self, name='embed')

    }


@FsiApp.view(
    model=Course,
    request_method='DELETE',
    permission=Secret
)
def delete_course(self: Course, request: FsiRequest) -> None:
    request.assert_valid_csrf_token()
    if not request.session.query(self.events.exists()).scalar():
        CourseCollection(request.session).delete(self)
        request.success(_('Course successfully deleted'))
    else:
        request.warning(_('This course has events and can not be deleted'))
