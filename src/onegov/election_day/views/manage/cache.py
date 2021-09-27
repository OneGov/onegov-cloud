from morepath import redirect
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import EmptyForm
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.manage_form(
    model=Principal,
    name='clear-cache',
    template='form.pt',
    form=EmptyForm
)
def view_clear_pages_cache(self, request, form):

    """ Clears the pages cache. """

    layout = DefaultLayout(self, request)

    if form.submitted(request):
        request.app.pages_cache.flush()
        request.message(_("Cache cleared."), 'success')
        return redirect(layout.manage_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("Clear cache"),
        'callout': _(
            "Elections and votes are cached for ${expiration} seconds. The "
            "cache is automatically cleared for new results and other "
            "updates. It is not normally necessary to clear the cache "
            "yourself.",
            mapping={'expiration': self.cache_expiration_time}
        ),
        'cancel': layout.manage_link
    }
