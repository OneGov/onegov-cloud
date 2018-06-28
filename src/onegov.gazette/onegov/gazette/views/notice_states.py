from mailthon.enclosure import Attachment
from morepath import redirect
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.templates import render_template
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import RejectForm
from onegov.gazette.layout import Layout
from onegov.gazette.layout import MailLayout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.views import get_user_and_group
from webob.exc import HTTPForbidden


def send_accepted_mail(request, notice):
    """ Sends a mail to the publisher with the contents of the notice.

    We use named temporary files because the files stored by depot does not
    have a nice filename (which is automatically used by mailton) and to allow
    temporary files from the memory without a real file on the disk.

    """

    def construct_subject(notice, request):
        issues = notice.issue_objects
        number = issues[0].number if issues else ''

        organization = notice.organization_object
        parent = organization.parent if organization else None
        parent_id = (parent.external_name or '') if parent else ''
        prefixes = []
        if notice.at_cost:
            prefixes.append(request.translate(_("With costs")))
        if notice.print_only:
            prefixes.append(request.translate(_("Print only")))
        prefix = '' if not prefixes else "{} - ".format(" / ".join(prefixes))

        return "{}{} {} {} {}".format(
            prefix, number, parent_id, notice.title, notice.id
        )

    reply_to = (
        request.app.principal.on_accept.get('mail_from') or
        request.app.mail['transactional']['sender']
    )

    subject = construct_subject(notice, request)
    content = render_template(
        'mail_on_accept.pt',
        request,
        {
            'title': subject,
            'model': notice,
            'layout': MailLayout(notice, request)
        }
    )

    attachments = []
    for file in notice.files:
        attachment = Attachment(file.reference.file._file_path)
        content_disposition = 'attachment; filename="{}"'.format(file.name)
        attachment.headers['Content-Disposition'] = content_disposition
        attachments.append(attachment)

    request.app.send_transactional_email(
        subject=subject,
        receivers=(request.app.principal.on_accept['mail_to'], ),
        reply_to=reply_to,
        content=content,
        attachments=attachments
    )


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

    If a notice has invalid/past issues or an invalid/inactive
    category/organization, the user is redirected to the edit view.

    """

    layout = Layout(self, request)
    is_private = request.is_private(self)

    if not is_private:
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
        self.expired_issues or
        (self.overdue_issues and not is_private) or
        self.invalid_category or
        self.invalid_organization
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

    if self.state != 'submitted' and self.state != 'imported':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Accept Official Note"),
            'callout': _("Only submitted official notices may be accepted."),
            'show_form': False
        }

    if (
        self.state == 'submitted' and (
            self.expired_issues or
            self.invalid_category or
            self.invalid_organization
        )
    ):
        return redirect(request.link(self, name='edit'))

    if form.submitted(request):
        self.accept(request)
        request.message(_("Official notice accepted."), 'success')
        if request.app.principal.on_accept and self.state != 'imported':
            send_accepted_mail(request, self)
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
            request.app.send_transactional_email(
                subject=request.translate(
                    _(
                        "Official Notice Rejected ${id}",
                        mapping={'id': self.id}
                    )
                ),
                receivers=(self.user.username, ),
                reply_to=request.app.mail['transactional']['sender'],
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
