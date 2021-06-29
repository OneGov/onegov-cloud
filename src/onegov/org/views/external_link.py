from onegov.org import _
from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.org.forms.external_link import ExternalLinkForm
from onegov.org.layout import ExternalLinkLayout, DefaultLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink
)
from morepath import redirect


def get_external_link_form(model, request):
    if isinstance(model, ExternalLinkCollection):
        model = model.model_class()
    return model.with_content_extensions(ExternalLinkForm, request)


@OrgApp.form(
    model=ExternalLinkCollection, name='new', template='form.pt',
    permission=Private, form=get_external_link_form
)
def handle_new_external_link(self, request, form, layout=None):
    if form.submitted(request):
        external_link = self.add_by_form(form)
        request.success(_("Added a new external form"))
        return redirect(request.class_link(
            ExternalLinkCollection.target(external_link)
        ))

    layout = layout or DefaultLayout(self, request)
    return {
        'layout': layout,
        'title': request.params.get('title', _("New external link")),
        'form': form,
    }


@OrgApp.form(model=ExternalLink, name='edit', template='form.pt',
             permission=Private, form=get_external_link_form)
def edit_external_link(self, request, form, layout=None):
    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        to = request.params.get('to')
        return redirect(to or request.link(request.app.org))

    form.process(obj=self)

    layout = layout or ExternalLinkLayout(self, request)
    return {
        'layout': layout,
        'title': request.params.get('title', _("Edit external link")),
        'form': form,
    }


@OrgApp.view(model=ExternalLink, permission=Private, request_method='DELETE')
def delete_external_link(self, request):
    request.assert_valid_csrf_token()
    request.session.delete(self)
