from onegov.core.html import html_to_text
from onegov.core.security import Private, Secret, Personal
from onegov.core.templates import render_template
from onegov.fsi import FsiApp
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.forms.course import CourseForm, InviteCourseForm
from onegov.fsi import _
from onegov.fsi.layouts.course import CourseCollectionLayout, CourseLayout, \
    AddCourseLayout, EditCourseLayout, InviteCourseLayout, \
    CourseInviteMailLayout
from onegov.fsi.models import CourseAttendee

from onegov.fsi.models.course import Course
from onegov.fsi.models.course_notification_template import \
    CourseInvitationTemplate, CourseNotificationTemplate
from onegov.user import User


def handle_send_invitation_email(
        self, course, request, recipients, cc_to_sender=True):
    """Recipients must be a list of emails"""

    if not recipients:
        request.alert(_("There are no recipients matching the selection"))
    else:
        att = request.attendee
        if cc_to_sender and att.id not in recipients:
            recipients = list(recipients)
            recipients.append(att.id)

        mail_layout = CourseInviteMailLayout(course, request)

        errors = []

        for email in recipients:

            attendee = request.session.query(
                CourseAttendee).filter_by(_email=email).first()
            if not attendee:
                user = request.session.query(User).filter_by(
                    username=email).first()
                if not user:
                    errors.append(email)
                    continue
                attendee = user.attendee
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
            plaintext = html_to_text(content)

            request.app.send_transactional_email(
                receivers=(attendee.email,),
                subject=self.subject,
                content=content,
                plaintext=plaintext,
            )

        request.success(_(
            "Successfully sent the e-mail to ${count} recipients",
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
    name='embed')
def view_email_preview_for_course(self, request):

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
def view_course_collection(self, request):
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
def view_add_course_event(self, request, form):
    layout = AddCourseLayout(self, request)
    layout.include_editor()

    if form.submitted(request):
        course = self.add(**form.get_useful_data())
        request.success(_("Added a new course"))
        return request.redirect(request.link(course))

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
def view_course_event(self, request):
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
def get_course_event_content(self, request):
    return self.description_html


@FsiApp.form(
    model=Course,
    template='form.pt',
    name='edit',
    form=CourseForm,
    permission=Secret
)
def view_edit_course_event(self, request, form):
    layout = EditCourseLayout(self, request)
    layout.include_editor()

    if form.submitted(request):
        form.update_model(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

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
def invite_attendees_for_event(self, request, form):
    layout = InviteCourseLayout(self, request)

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
def delete_course(self, request):
    request.assert_valid_csrf_token()
    if not self.events.first():
        CourseEventCollection(request.session).delete(self)
        request.success(_('Course successfully deleted'))
    else:
        request.warning(_('This course has events and can not be deleted'))
