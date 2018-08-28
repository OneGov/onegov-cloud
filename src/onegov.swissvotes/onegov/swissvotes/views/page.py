from onegov.core.security import Private
from onegov.core.security import Public
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.forms import PageForm
from onegov.swissvotes.layouts import EditPageLayout
from onegov.swissvotes.layouts import PageLayout
from onegov.swissvotes.models import TranslatablePage


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
