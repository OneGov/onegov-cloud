from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.forms import UnrestrictedNoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.pdf import NoticesPdf
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

    user_ids, group_ids = get_user_and_group(request)
    editor = request.is_personal(self)
    publisher = request.is_private(self)
    admin = request.is_secret(self)
    owner = self.user_id in user_ids
    same_group = self.group_id in group_ids

    def _action(label, name, class_, target='_self'):
        return (label, request.link(self, name), class_, target)

    action = {
        'accept': _action(_("Accept"), 'accept', 'primary'),
        'attachments': _action(_("Attachments"), 'attachments', 'secondary'),
        'copy': (
            _("Copy"),
            request.link(
                GazetteNoticeCollection(
                    request.session,
                    state=self.state,
                    source=self.id
                ), name='new-notice'
            ),
            'secondary',
            '_self'
        ),
        'delete': _action(_("Delete"), 'delete', 'alert right'),
        'edit_un': _action(_("Edit"), 'edit-unrestricted', 'secondary'),
        'edit': _action(_("Edit"), 'edit', 'secondary'),
        'preview': _action(_("Preview"), 'preview', 'secondary', '_blank'),
        'reject': _action(_("Reject"), 'reject', 'alert right'),
        'submit': _action(_("Submit"), 'submit', 'primary'),
    }

    actions = []
    if self.state == 'drafted' or self.state == 'rejected':
        if publisher or (editor and (same_group or owner)):
            actions.append(action['submit'])
            actions.append(action['edit'])
            actions.append(action['delete'])
        if publisher:
            actions.append(action['attachments'])
    elif self.state == 'submitted':
        if publisher:
            actions.append(action['accept'])
            actions.append(action['edit'])
            actions.append(action['reject'])
            actions.append(action['attachments'])
        if admin:
            actions.append(action['delete'])
    elif self.state == 'accepted':
        actions.append(action['copy'])
        if publisher:
            actions.append(action['edit_un'])
        if admin:
            actions.append(action['attachments'])
        if publisher:
            actions.append(action['delete'])
    elif self.state == 'imported':
        if publisher:
            actions.append(action['accept'])
            actions.append(action['delete'])
    elif self.state == 'published':
        actions.append(action['copy'])
        if publisher:
            actions.append(action['edit_un'])
        if admin:
            actions.append(action['attachments'])

    actions.append(action['preview'])

    return {
        'layout': layout,
        'notice': self,
        'actions': actions,
        'publisher': publisher
    }


@GazetteApp.html(
    model=GazetteNotice,
    template='preview.pt',
    name='preview',
    permission=Personal
)
def preview_notice(self, request):
    """ Preview the notice. """

    layout = Layout(self, request)

    return {
        'layout': layout,
        'notice': self,
        'export': request.link(self, name='preview-pdf')
    }


@GazetteApp.view(
    model=GazetteNotice,
    name='preview-pdf',
    permission=Personal
)
def preview_notice_pdf(self, request):
    """ Preview the notice as PDF. """

    pdf = NoticesPdf.from_notice(self, request)

    filename = normalize_for_url(
        '{}-{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name,
            self.title
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )


@GazetteApp.form(
    model=GazetteNotice,
    name='edit',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def edit_notice(self, request, form):
    """ Edit a notice.

    This view is used by the editors and publishers. Editors may only edit
    their own notices, publishers may edit any notice. It's not possible to
    change already accepted or published notices (although you can use the
    unrestricted view for this).

    """

    layout = Layout(self, request)
    is_private = request.is_private(self)

    if not is_private:
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if self.state == 'accepted' or self.state == 'published':
        return {
            'layout': layout,
            'title': self.title,
            'subtitle': _("Edit Official Notice"),
            'callout': _(
                "Accepted official notices may not be edited."
            ),
            'show_form': False
        }

    if self.expired_issues:
        request.message(
            _(
                "The official notice has past issue. Please re-select issues."
            ),
            'warning'
        )
    elif self.overdue_issues and not is_private:
        request.message(
            _(
                "The official notice has issues for which the deadlines are "
                "reached. Please re-select valid issues."
            ),
            'warning'
        )
    if self.invalid_category:
        request.message(
            _(
                "The official notice has an invalid category. "
                "Please re-select the category."
            ),
            'warning'
        )
    if self.invalid_organization:
        request.message(
            _(
                "The official notice has an invalid organization. "
                "Please re-select the organization."
            ),
            'warning'
        )

    if form.submitted(request):
        form.update_model(self)
        self.add_change(request, _("edited"))
        request.message(_("Official notice modified."), 'success')
        return redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Official Notice"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': request.link(self),
        'current_issue': layout.current_issue
    }


@GazetteApp.form(
    model=GazetteNotice,
    name='edit-unrestricted',
    template='form.pt',
    permission=Private,
    form=UnrestrictedNoticeForm
)
def edit_notice_unrestricted(self, request, form):
    """ Edit a notice without restrictions.

    This view is only usable by publishers.

    """

    layout = Layout(self, request)

    if self.state == 'published':
        form.disable_issues()

    if form.submitted(request):
        form.update_model(self)
        self.add_change(request, _("edited"))
        request.message(_("Official notice modified."), 'success')
        return redirect(request.link(self))

    if self.state == 'accepted':
        request.message(
            _("This official notice has already been accepted!"), 'warning'
        )
    elif self.state == 'published':
        request.message(
            _("This official notice has already been published!"), 'warning'
        )

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'subtitle': _("Edit Official Notice"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': request.link(self)
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

    Editors may only delete their own drafted and rejected notices.

    Publishers may delete any drafted, rejected and accepted notices.

    Admins may delete any drafted, submitted, rejected and accepted notices.

    """
    layout = Layout(self, request)
    is_secret = request.is_secret(self)
    is_private = request.is_private(self)

    if not is_private:
        user_ids, group_ids = get_user_and_group(request)
        if not ((self.group_id in group_ids) or (self.user_id in user_ids)):
            raise HTTPForbidden()

    if (
        (self.state == 'submitted' and not is_secret)
        or (self.state == 'accepted' and not is_private)
        or (self.state == 'published')
    ):
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

    if self.state == 'accepted':
        request.message(
            _("This official notice has already been accepted!"), 'warning'
        )

    if form.submitted(request):
        collection = GazetteNoticeCollection(request.session)
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
