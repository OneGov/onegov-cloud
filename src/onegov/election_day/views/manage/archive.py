from __future__ import annotations

from morepath import redirect
from onegov.core.security import Secret
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.forms import EmptyForm
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.manage_form(
    model=Principal,
    name='update-results',
    template='form.pt',
    form=EmptyForm,
    permission=Secret
)
def view_update_results(
    self: Principal,
    request: ElectionDayRequest,
    form: EmptyForm
) -> RenderData | Response:
    """ Updates all archived results. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        archive = ArchivedResultCollection(request.session)
        archive.update_all(request)
        request.message(_('Results updated.'), 'success')
        return redirect(layout.manage_link)

    return {
        'layout': layout,
        'form': form,
        'title': _('Update archived results'),
        'callout': _(
            'The results on the home page and in the archive are cached and '
            'need to be updated after a domain change, for example.'
        ),
        'cancel': layout.manage_link
    }
