from onegov.core.security import Private
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.layout import Layout


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='notices.pt',
    permission=Private
)
def view_notices(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'published')
    is the view used by the publisher.

    """

    layout = Layout(self, request)

    title = {
        'submitted': _("Submitted Official Notices"),
        'published': _("Published Official Notices")
    }.get(self.state, _("Official Notices"))

    return {
        'layout': layout,
        'state': self.state,
        'notices': self.batch,
        'title': title
    }
