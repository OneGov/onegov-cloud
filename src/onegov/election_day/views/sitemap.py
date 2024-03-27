from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=Principal,
    name='sitemap.xml',
    template='sitemap.xml.pt',
    permission=Public
)
def view_sitemap_xml(
    self: Principal,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """ Returns a XML-sitemap.

    See https://www.sitemaps.org for more information.

    """

    @request.after
    def add_headers(response: 'Response') -> None:
        response.headers['Content-Type'] = 'application/xml'

    layout = DefaultLayout(self, request)

    def urls() -> 'Iterator[str]':
        yield request.link(self)
        yield layout.archive_search_link
        if layout.principal.email_notification:
            yield request.link(self, 'subscribe-email')
            yield request.link(self, 'unsubscribe-email')
        if layout.principal.sms_notification:
            yield request.link(self, 'subscribe-sms')
            yield request.link(self, 'unsubscribe-sms')
        for year in layout.archive.get_years():
            yield request.link(layout.archive.for_date(str(year)))

            archive = ArchivedResultCollection(request.session, str(year))
            results, last_modified = archive.by_date()
            grouped_results = archive.group_items(results, request) or {}
            for date_, domains in grouped_results.items():
                yield request.link(layout.archive.for_date(date_.isoformat()))
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
def view_sitemap(
    self: Principal,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """ Returns a site map (with hiearchy). """

    layout = DefaultLayout(self, request)

    return {
        'layout': layout
    }
