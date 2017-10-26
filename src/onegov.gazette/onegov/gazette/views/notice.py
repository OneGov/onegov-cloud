from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.forms import RejectForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.views import get_user_and_group
from webob.exc import HTTPForbidden


@GazetteApp.html(
    model=GazetteNotice,
    template='notice.pt',
    permission=Personal
)
def view_notice(self, request):
    """ View a notice.

    View the notice and its meta data. This is the main view for the notices
    to do the state changes.

    """

    layout = Layout(self, request)

    actions = []

    user_ids, group_ids = get_user_and_group(request)
    editor = request.is_personal(self)
    publisher = request.is_private(self)
    owner = self.user_id in user_ids
    same_group = self.group_id in group_ids

    if self.state == 'drafted' or self.state == 'rejected':
        if publisher or (editor and (same_group or owner)):
            actions.append((
                _("Submit"),
                request.link(self, 'submit'),
                'primary',
                '_self'
            ))
            actions.append((
                _("Edit"),
                request.link(self, 'edit'),
                'secondary',
                '_self'
            ))
            actions.append((
                _("Delete"),
                request.link(self, 'delete'),
                'alert right',
                '_self'
            ))

    if self.state == 'submitted':
        if publisher:
            actions.append((
                _("Accept"),
                request.link(self, 'accept'),
                'primary',
                '_self'
            ))
            actions.append((
                _("Edit"),
                request.link(self, 'edit'),
                'secondary',
                '_self'
            ))
            actions.append((
                _("Reject"),
                request.link(self, 'reject'),
                'alert right',
                '_self'
            ))

    if self.state == 'accepted':
        actions.append((
            _("Copy"),
            request.link(
                GazetteNoticeCollection(
                    request.app.session(),
                    state=self.state,
                    source=self.id
                ), name='new-notice'
            ),
            'secondary',
            '_self'
        ))

    actions.append((
        _("Preview"),
        request.link(self, 'preview'),
        'secondary',
        '_blank'
    ))

    return {
        'layout': layout,
        'notice': self,
        'actions': actions
    }


@GazetteApp.html(
    model=GazetteNotice,
    template='preview.pt',
    name='preview',
    permission=Personal
)
def view_notice_preview(self, request):
    """ Preview the notice. """

    layout = Layout(self, request)

    return {
        'layout': layout,
        'notice': self
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='edit',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def edit_notice(self, request, form):
    """ Edit a notice.

    The issue can not be changed. This view is used by the editors and
    publishers. Editors may only edit their own notices, publishers may edit
    any notice.

    """

    layout = Layout(self, request)

    if not request.is_private(self):
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.state == 'accepted' or self.state == 'published':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Edit Official Notice"),
            'callout': _(
                'Accepted official notices may not be edited.'
            ),
            'show_form': False
        }

    if self.expired_issues(request.app.principal):
        request.message(
            _(
                "The official notice has past issue. Please re-select issues."
            ),
            'warning'
        )
    elif (
        self.overdue_issues(request.app.principal) and
        not request.is_private(self)
    ):
        request.message(
            _(
                "The official notice has issues for which the deadlines are "
                "reached. Please re-select valid issues."
            ),
            'warning'
        )

    if form.submitted(request):
        form.update_model(self)
        self.add_change(request, _("edited"))
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Official Notice"),
        'button_text': _("Save"),
        'cancel': request.link(self),
        'current_issue': request.app.principal.current_issue
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='delete',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def delete_notice(self, request, form):
    """ Delete a notice.

    Only drafted or rejected notices may be deleted (usually by editors).
    Editors may only delete their own notices, publishers may delete any
    notice.

    It is possible for admins to delete accepted/published and drafted notices
    too, although the action is not linked anywhere.

    """
    layout = Layout(self, request)

    if not request.is_private(self):
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.state != 'drafted' and self.state != 'rejected':
        if request.is_secret(self):
            request.message(
                _(
                    "It's probably not a good idea to delete this official "
                    "notice!"
                ),
                'warning'
            )
        else:
            request.message(
                _(
                    "Only drafted or rejected official notices may be deleted."
                ),
                'alert'
            )
            return {
                'layout': layout,
                'title': self.title,
                'subtitle': _("Delete Official Notice"),
                'show_form': False
            }

    if form.submitted(request):
        collection = GazetteNoticeCollection(request.app.session())
        collection.delete(self)
        request.message(_("Official notice deleted."), 'success')
        return redirect(layout.dashboard_or_notices_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Delete Official Notice"),
        'button_text': _("Delete Official Notice"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='submit',
    template='form.pt',
    permission=Personal,
    form=EmptyForm
)
def submit_notice(self, request, form):
    """ Submit a notice.

    This view is used by the editors to submit their drafts for the publishers
    to review.

    Only drafted notices may be submitted. Editors may only submit their own
    notices (publishers may submit any notice).

    If a notice has invalid/past issues, the user is redirected to the edit
    view to select new issues.

    """

    layout = Layout(self, request)

    if not request.is_private(self):
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.state != 'drafted' and self.state != 'rejected':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Submit Official Note"),
            'callout': _(
                "Only drafted or rejected official notices may be submitted."
            ),
            'show_form': False
        }

    if (
        self.expired_issues(request.app.principal) or
        (
            self.overdue_issues(request.app.principal) and
            not request.is_private(self)
        )
    ):
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.submit(request)
        request.message(_("Official notice submitted."), 'success')
        return redirect(layout.dashboard_or_notices_link)

    return {
        'message': _(
            'Do you really want to submit "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Submit Official Note"),
        'button_text': _("Submit Official Note"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='accept',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def accept_notice(self, request, form):
    """ Accept a notice.

    This view is used by the publishers to accept a submitted notice.

    Only submitted notices may be accepted.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Accept Official Note"),
            'callout': _("Only submitted official notices may be accepted."),
            'show_form': False
        }

    if self.expired_issues(request.app.principal):
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.accept(request)
        request.message(_("Official notice accepted."), 'success')
        if request.app.principal.publish_to:
            reply_to = (
                request.app.principal.publish_from or request.app.mail_sender
            )
            issues = list(self.issues.keys())
            number = Issue.from_string(issues[0]).number if issues else ''
            subject = "{} {} {}".format(number, self.title, self.id)
            request.app.send_email(
                subject=subject,
                receivers=(request.app.principal.publish_to, ),
                reply_to=reply_to,
                content=render_template(
                    'mail_publish.pt',
                    request,
                    {
                        'title': subject,
                        'model': self,
                        'layout': MailLayout(self, request)
                    }
                )
            )
            self.add_change(request, _("mail sent"))
        return redirect(layout.dashboard_or_notices_link)

    return {
        'message': _(
            'Do you really want to accept "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Accept Official Note"),
        'button_text': _("Accept Official Note"),
        'cancel': request.link(self)
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='reject',
    template='form.pt',
    permission=Private,
    form=RejectForm
)
def reject_notice(self, request, form):
    """ Reject a notice.

    This view is used by the publishers to reject a submitted notice.

    Only submitted notices may be rejected.

    """

    layout = Layout(self, request)

    if self.state != 'submitted':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Reject Official Note"),
            'callout': _("Only submitted official notices may be rejected."),
            'show_form': False
        }

    if form.submitted(request):
        self.reject(request, form.comment.data)
        request.message(_("Official notice rejected."), 'success')
        if self.user:
            request.app.send_email(
                subject=request.translate(
                    _(
                        "Official Notice Rejected ${id}",
                        mapping={'id': self.id}
                    )
                ),
                receivers=(self.user.username, ),
                reply_to=request.app.mail_sender,
                content=render_template(
                    'mail_notice_rejected.pt',
                    request,
                    {
                        'title': request.translate(_(
                            "Official Notice Rejected ${id}",
                            mapping={'id': self.id}
                        )),
                        'model': self,
                        'comment': form.comment.data,
                        'layout': MailLayout(self, request),
                        'url': request.link(self)
                    }
                )
            )
        return redirect(layout.dashboard_or_notices_link)

    return {
        'message': _(
            'Do you really want to reject "${item}"?',
            mapping={'item': self.title}
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Reject Official Note"),
        'button_text': _("Reject Official Note"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
