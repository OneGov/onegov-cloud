from onegov.core.security import Private
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.layout import MatchCollectionLayout


@FeriennetApp.html(
    model=MatchCollection,
    template='matches.pt',
    permission=Private)
def view_matches(self, request):

    layout = MatchCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': _("Matches for ${title}", mapping={
            'title': self.period.title
        }),
        'occasions': self.occasions
    }
