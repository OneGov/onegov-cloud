from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.forms import AssemblyForm
from onegov.landsgemeinde.layouts import AssemblyCollectionLayout
from onegov.landsgemeinde.layouts import AssemblyLayout
from onegov.landsgemeinde.models import Assembly


@LandsgemeindeApp.html(
    model=AssemblyCollection,
    template='assemblies.pt',
    permission=Public
)
def view_assemblies(self, request):

    layout = AssemblyCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'assemblies': self.query().all(),
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=AssemblyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AssemblyForm
)
def add_assembly(self, request, form):

    if form.submitted(request):
        assembly = self.add(**form.get_useful_data())
        request.success(_("Added a new assembly"))

        return redirect(request.link(assembly))

    layout = AssemblyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New assembly"),
        'form': form,
    }


@LandsgemeindeApp.html(
    model=Assembly,
    template='assembly.pt',
    permission=Public
)
def view_assembly(self, request):

    layout = AssemblyLayout(self, request)

    return {
        'layout': layout,
        'assembly': self,
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=Assembly,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AssemblyForm
)
def edit_assembly(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AssemblyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=Assembly,
    request_method='DELETE',
    permission=Private
)
def delete_assembly(self, request):

    request.assert_valid_csrf_token()

    collection = AssemblyCollection(request.session)
    collection.delete(self)
