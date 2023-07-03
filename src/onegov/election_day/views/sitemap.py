from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


@ElectionDayApp.view(
    model=Principal,
    name='sitemap.xml',
    template='sitemap.xml.pt',
    permission=Public
)
def view_sitemap_xml(self, request):

    """ Returns a XML-sitemap.

    See https://www.sitemaps.org for more information.

    """

    @request.after
    def add_headers(response):
        response.headers['Content-Type'] = 'application/xml'

    layout = DefaultLayout(self, request)

    def urls():
        yield request.link(self)
        yield layout.archive_search_link
        if layout.principal.email_notification:
            yield request.link(self, 'subscribe-email')
            yield request.link(self, 'unsubscribe-email')
        if layout.principal.sms_notification:
            yield request.link(self, 'subscribe-sms')
            yield request.link(self, 'unsubscribe-sms')
        for year in layout.archive.get_years():
            yield request.link(layout.archive.for_date(year))

            archive = ArchivedResultCollection(request.session, year)
            results, last_modified = archive.by_date()
            results = archive.group_items(results, request)
            for date_, domains in results.items():
                yield request.link(layout.archive.for_date(date_))
                for items in domains.values():
                    for value in items.values():
                        for result in value:
                            yield result.adjusted_url(request)

    return {'urls': sorted(urls())}


@ElectionDayApp.html(
    model=Principal,
    name='sitemap',
    template='sitemap.pt',
    permission=Public
)
def view_sitemap(self, request):

    """ Returns a site map (with hiearchy). """

    layout = DefaultLayout(self, request)

    return {
        'layout': layout
    }
