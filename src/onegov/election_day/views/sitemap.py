from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models import Principal
from onegov.election_day.security import MaybePublic


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def urls(
    principal: Principal,
    request: ElectionDayRequest
) -> Iterator[str]:
    layout = DefaultLayout(principal, request)

    yield request.link(principal)
    yield layout.archive_search_link
    if layout.principal.email_notification:
        yield request.link(principal, 'subscribe-email')
        yield request.link(principal, 'unsubscribe-email')
    if layout.principal.sms_notification:
        yield request.link(principal, 'subscribe-sms')
        yield request.link(principal, 'unsubscribe-sms')
    for year in layout.archive.get_years():
        yield request.link(layout.archive.for_date(str(year)))

        archive = ArchivedResultCollection(request.session, str(year))
        results, _last_modified = archive.by_date()
        grouped_results = archive.group_items(results, request) or {}
        for date_, domains in grouped_results.items():
            yield request.link(layout.archive.for_date(date_.isoformat()))
            for items in domains.values():
                for value in items.values():
                    for result in value:
                        yield result.adjusted_url(request)


@ElectionDayApp.view(
    model=Principal,
    name='sitemap.xml',
    template='sitemap.xml.pt',
    permission=MaybePublic
)
def view_sitemap_xml(
    self: Principal,
    request: ElectionDayRequest
) -> RenderData:
    """ Returns a XML-sitemap.

    See https://www.sitemaps.org for more information.

    """

    @request.after
    def add_headers(response: Response) -> None:
        response.headers['Content-Type'] = 'application/xml'

    return {'urls': sorted(urls(self, request))}


@ElectionDayApp.json(
    model=Principal,
    name='sitemap.json',
    permission=MaybePublic
)
def view_sitemap_json(
    self: Principal,
    request: ElectionDayRequest
) -> RenderData:
    """ Returns the XML-sitemap as json. """

    return {'urls': sorted(urls(self, request))}


@ElectionDayApp.html(
    model=Principal,
    name='sitemap',
    template='sitemap.pt',
    permission=MaybePublic
)
def view_sitemap(
    self: Principal,
    request: ElectionDayRequest
) -> RenderData:
    """ Returns a site map (with hiearchy). """

    layout = DefaultLayout(self, request)

    return {
        'layout': layout
    }
