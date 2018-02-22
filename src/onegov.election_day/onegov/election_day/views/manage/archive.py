from morepath import redirect
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.forms import EmptyForm
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.manage_form(
    model=Principal,
    name='update-results',
    template='form.pt',
    form=EmptyForm
)
def view_update_results(self, request, form):

    """ Updates all results.

    This view is not linked anywhere since there is normally no need to call
    it.

    """

    layout = DefaultLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive = ArchivedResultCollection(request.session)
        archive.update_all(request)
        request.message(_("Results updated."), 'success')
        return redirect(layout.manage_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("Update results"),
        'cancel': layout.manage_link
    }
