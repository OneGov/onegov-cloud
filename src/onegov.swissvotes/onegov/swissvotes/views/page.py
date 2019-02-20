from morepath import redirect
from onegov.core.crypto import random_token
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.forms import PageForm
from onegov.swissvotes.layouts import AddPageLayout
from onegov.swissvotes.layouts import DeletePageAttachmentLayout
from onegov.swissvotes.layouts import DeletePageLayout
from onegov.swissvotes.layouts import EditPageLayout
from onegov.swissvotes.layouts import PageAttachmentsLayout
from onegov.swissvotes.layouts import PageLayout
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageFile
from onegov.swissvotes.models import TranslatablePageMove
from webob import exc


@SwissvotesApp.html(
    model=TranslatablePage,
    template='page.pt',
    permission=Public
)
def view_page(self, request):
    """ View a page. """

    files = [file for file in self.files if file.locale == request.locale]
    return {
        'layout': PageLayout(self, request),
        'files': files
    }


@SwissvotesApp.form(
    model=TranslatablePageCollection,
    permission=Private,
    form=PageForm,
    template='form.pt',
    name='add'
)
def add_page(self, request, form):
    request.include('quill')

    if form.submitted(request):
        page = TranslatablePage()
        form.update_model(page)
        request.session.add(page)
        request.message(_("Page added."), 'success')
        return request.redirect(request.link(page))

    return {
        'layout': AddPageLayout(self, request),
        'form': form
    }


@SwissvotesApp.form(
    model=TranslatablePage,
    permission=Private,
    form=PageForm,
    template='form.pt',
    name='edit'
)
def edit_page(self, request, form):
    request.include('quill')

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Page modified."), 'success')
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': EditPageLayout(self, request),
        'form': form
    }


@SwissvotesApp.form(
    model=TranslatablePage,
    permission=Private,
    form=Form,
    template='form.pt',
    name='delete'
)
def delete_vote(self, request, form):
    layout = DeletePageLayout(self, request)

    if form.submitted(request):
        request.session.delete(self)
        request.message(_("Page deleted"), 'success')
        return request.redirect(layout.homepage_url)

    return {
        'layout': layout,
        'form': form,
        'subtitle': self.title,
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.title}
        ),
        'button_text': _("Delete"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }


@SwissvotesApp.view(
    model=TranslatablePageMove,
    permission=Private,
    request_method='PUT'
)
def move_page(self, request):
    request.assert_valid_csrf_token()
    self.execute()


@SwissvotesApp.html(
    model=TranslatablePage,
    template='attachments.pt',
    name='attachments',
    permission=Private
)
def view_page_attachments(self, request):
    """ View all attachments of a page and allow to drop new attachments. """

    layout = PageAttachmentsLayout(self, request)
    upload_url = layout.csrf_protected_url(request.link(self, name='upload'))
    files = [file for file in self.files if file.locale == request.locale]

    return {
        'layout': layout,
        'title': self.title,
        'subtitle': _("Attachments"),
        'upload_url': upload_url,
        'files': files,
        'notice': self,
    }


@SwissvotesApp.view(
    model=TranslatablePage,
    name='upload',
    permission=Private,
    request_method='POST'
)
def upload_page_attachment(self, request):
    """ Upload an attachment and add it to the page.

    Raises a HTTP 415 (Unsupported Media Type) if the file format is not
    supported.

    """

    request.assert_valid_csrf_token()

    attachment = TranslatablePageFile(id=random_token())
    attachment.name = '{}-{}'.format(
        request.locale,
        request.params['file'].filename
    )
    attachment.reference = as_fileintent(
        request.params['file'].file,
        request.params['file'].filename
    )

    if attachment.reference.content_type != 'application/pdf':
        raise exc.HTTPUnsupportedMediaType()

    self.files.append(attachment)
    request.message(_("Attachment added."), 'success')
    return redirect(request.link(self, 'attachments'))


@SwissvotesApp.form(
    model=TranslatablePageFile,
    name='delete',
    template='form.pt',
    permission=Private,
    form=Form
)
def delete_page_attachment(self, request, form):
    """ Delete an attachment. """

    layout = DeletePageAttachmentLayout(self, request)

    if form.submitted(request):
        url = request.link(self.linked_swissvotes_page[0], 'attachments')
        request.session.delete(self)
        request.message(_("Attachment deleted."), 'success')
        return redirect(url)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={'item': self.filename}
        ),
        'layout': layout,
        'form': form,
        'title': self.filename,
        'subtitle': _("Delete"),
        'button_text': _("Delete"),
        'button_class': 'alert',
        'cancel': request.link(self)
    }
