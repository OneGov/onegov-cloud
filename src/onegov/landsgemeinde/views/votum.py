from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.forms import VotumForm
from onegov.landsgemeinde.layouts import VotumCollectionLayout
from onegov.landsgemeinde.layouts import VotumLayout
from onegov.landsgemeinde.models import Votum


@LandsgemeindeApp.form(
    model=VotumCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=VotumForm
)
def add_votum(self, request, form):

    if form.submitted(request):
        votum = self.add(**form.get_useful_data())
        request.success(_("Added a new votum"))

        return redirect(
            request.link(votum.agenda_item, fragment=f'votum-{votum.number}'),
        )

    form.number.data = form.next_number

    layout = VotumCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New votum"),
        'form': form,
    }


@LandsgemeindeApp.form(
    model=Votum,
    name='edit',
    template='form.pt',
    permission=Private,
    form=VotumForm
)
def edit_votum(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(
            request.link(self.agenda_item, fragment=f'votum-{self.number}')
        )

    form.process(obj=self)

    layout = VotumLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=Votum,
    request_method='DELETE',
    permission=Private
)
def delete_votum(self, request):

    request.assert_valid_csrf_token()

    collection = VotumCollection(request.session)
    collection.delete(self)
