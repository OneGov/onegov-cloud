from morepath import redirect
from onegov.core.crypto import random_token
from onegov.core.security import Private
from onegov.file.utils import as_fileintent
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.forms import EmptyForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import GazetteNoticeFile
from webob import exc


@GazetteApp.html(
    model=GazetteNotice,
    template='attachments.pt',
    name='attachments',
    permission=Private
)
def view_notice_attachments(self, request):
    """ View all attachments to a single notice and allow to drop new
    attachments.

    Silently redirects to the notice view if the notice has already been
    accepted for non-admins.

    """

    layout = Layout(self, request)
    upload_url = layout.csrf_protected_url(request.link(self, name='upload'))

    if self.state == 'accepted' or self.state == 'published':
        if not request.is_secret(self):
            return redirect(request.link(self))

    return {
        'layout': layout,
        'title': self.title,
        'subtitle': _("Attachments"),
        'upload_url': upload_url,
        'files': self.files,
        'notice': self,
    }


@GazetteApp.view(
    model=GazetteNotice,
    name='upload',
    permission=Private,
    request_method='POST'
)
def upload_attachment(self, request):
    """ Upload an attachment and add it to the notice.

    Raises a HTTP 405 (Metho not Allowed) for non-admins if the notice has
    already been accepted.

    Raises a HTTP 415 (Unsupported Media Type) if the file format is not
    supported.

    """

    if self.state == 'accepted' or self.state == 'published':
        if not request.is_secret(self):
            raise exc.HTTPMethodNotAllowed()

    request.assert_valid_csrf_token()

    attachment = GazetteNoticeFile(id=random_token())
    attachment.name = request.params['file'].filename
    attachment.reference = as_fileintent(
        request.params['file'].file,
        request.params['file'].filename
    )

    if attachment.reference.content_type != 'application/pdf':
        raise exc.HTTPUnsupportedMediaType()

    self.files.append(attachment)
    self.add_change(request, _("Attachment added."))

    request.message(_("Attachment added."), 'success')
    return redirect(request.link(self, 'attachments'))


@GazetteApp.form(
    model=GazetteNoticeFile,
    name='delete',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def delete_attachment(self, request, form):
    """ Delete a notice attachment. """

    layout = Layout(self, request)

    notice = self.linked_official_notices[0]
    if notice.state == 'accepted' or notice.state == 'published':
        if not request.is_secret(self):
            request.message(
                _("Attachments of accepted notices can not be deleted."),
                'alert'
            )
            return {
                'layout': layout,
                'title': self.name,
                'subtitle': _("Delete"),
                'show_form': False
            }

    if form.submitted(request):
        url = request.link(self.linked_official_notices[0], 'attachments')
        request.session.delete(self)
        request.message(_("Attachment deleted."), 'success')
        notice.add_change(request, _("Attachment deleted."))
        return redirect(url)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.name}
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete"),
        'button_text': _("Delete"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
