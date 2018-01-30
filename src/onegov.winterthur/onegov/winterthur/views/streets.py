from itertools import groupby
from onegov.core.cache import lru_cache
from onegov.core.security import Public, Private
from onegov.winterthur import WinterthurApp, _
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.collections import AddressSubsetCollection
from onegov.winterthur.layout import AddressLayout
from onegov.winterthur.layout import AddressSubsetLayout


@WinterthurApp.html(
    model=AddressCollection,
    permission=Public,
    template='streets.pt'
)
def view_streets(self, request):
    request.include('street-search')
    request.include('iframe-resizer')

    by_letter = {
        letter: tuple(streets) for letter, streets in groupby(
            self.streets(), lambda s: s.letter
        )
    }

    @lru_cache(maxsize=1)
    def link_to_street(street):
        return request.class_link(AddressSubsetCollection, {'street': street})

    return {
        'layout': AddressLayout(self, request),
        'title': _("Streets Directory"),
        'streets': by_letter,
        'link_to_street': link_to_street
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


@WinterthurApp.html(
    model=AddressSubsetCollection,
    permission=Public,
    template='street.pt'
)
def view_street(self, request):
    request.include('iframe-resizer')

    return {
        'layout': AddressSubsetLayout(self, request),
        'title': self.street,
        'addresses': self.subset(),
        'parent': request.class_link(AddressCollection)
    }
