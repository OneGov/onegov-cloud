from onegov.core.security import Private
from onegov.core.security import Public
from onegov.form import Form
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.forms import PageForm
from onegov.swissvotes.layouts import AddPageLayout
from onegov.swissvotes.layouts import DeletePageLayout
from onegov.swissvotes.layouts import EditPageLayout
from onegov.swissvotes.layouts import PageLayout
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageMove


@SwissvotesApp.html(
    model=TranslatablePage,
    template='page.pt',
    permission=Public
)
def view_page(self, request):
    """ View a page. """

    return {
        'layout': PageLayout(self, request),
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
