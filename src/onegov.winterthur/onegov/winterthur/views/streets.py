from itertools import groupby
from onegov.core.security import Public, Private
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.layout import AddressLayout


@WinterthurApp.html(
    model=AddressCollection,
    permission=Public,
    template='streets.pt'
)
def view_streets(self, request):
    by_letter = {
        letter: tuple(streets) for letter, streets in groupby(
            self.streets(), lambda s: s.letter
        )
    }

    return {
        'layout': AddressLayout(self, request),
        'title': _("Streets Directory"),
        'streets': by_letter
    }


@WinterthurApp.view(
    model=AddressCollection,
    permission=Private,
    request_method='POST',
    name="update"
)
def update_streets(self, request):
    request.assert_valid_csrf_token()

    self.update()

    request.success(_("The streets directory has been updated"))
