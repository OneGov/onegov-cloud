from onegov.org import _
from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.org.forms.external_link import ExternalLinkForm
from onegov.org.layout import DefaultLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink
)
from morepath import redirect


@OrgApp.form(model=ExternalLinkCollection, name='new', template='form.pt',
             permission=Private, form=ExternalLinkForm)
def handle_new_external_link(self, request, form, layout=None):
    if form.submitted(request):
        self.add_by_form(form)
        request.success(_("Added a new external form"))
        to = request.params.get('to')
        return redirect(to or request.link(request.app.org))

    layout = layout or DefaultLayout(self, request)
    return {
        'layout': layout,
        'title': request.params.get('title', _("New external link")),
        'form': form,
    }


@OrgApp.form(model=ExternalLink, name='edit', template='form.pt',
             permission=Private, form=ExternalLinkForm)
def edit_external_link(self, request, form, layout=None):
    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        to = request.params.get('to')
        return redirect(to or request.link(request.app.org))

    layout = layout or DefaultLayout(self, request)
    return {
        'layout': layout,
        'title': request.params.get('title', _("Edit external link")),
        'form': form,
    }
