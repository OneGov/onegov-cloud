from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.view(
    model=Principal,
    name='sitemap.xml',
    template='sitemap.pt',
    permission=Public
)
def view_rdf(self, request):

    """ Returns a XML-sitemap.

    See https://www.sitemaps.org for moreinformation.

    """

    layout = DefaultLayout(self, request)
    urls = [
        request.link(self),
        layout.archive_search_link
    ]

    if layout.principal.email_notification:
        urls.extend((
            request.link(self, 'subscribe-email'),
            request.link(self, 'unsubscribe-email')
        ))
    if layout.principal.email_notification:
        urls.extend((
            request.link(self, 'subscribe-sms'),
            request.link(self, 'unsubscribe-sms')
        ))
    urls.extend((
        request.link(layout.archive.for_date(year))
        for year in layout.archive.get_years()
    ))

    return {'urls': urls}
