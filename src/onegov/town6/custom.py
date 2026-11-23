from onegov.core.elements import Link, LinkGroup
from onegov.org.custom import get_api_endpoints as get_api_endpoints_base
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.org.custom import get_modules as get_modules_base
from onegov.town6 import _
from onegov.town6.api import (
    CommissionApiEndpoint, MeetingApiEndpoint, ParliamentarianApiEndpoint,
    ParliamentaryGroupApiEndpoint, PoliticalBusinessApiEndpoint)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.api.models import ApiEndpoint
    from onegov.town6.request import TownRequest


def get_global_tools(request: TownRequest) -> Iterator[Link | LinkGroup]:
    for item in get_global_tools_base(request):

        classes = getattr(item, 'attrs', {}).get('class')
        if classes == {'login'} or classes == {'citizen-login'}:
            continue

        yield item


def get_modules(request: TownRequest) -> LinkGroup:
    modules = get_modules_base(request)
    links = list(modules.links)
    if request.is_admin and request.app.org.ris_enabled:
        links.append(
            Link(
                _('RIS Settings'),
                request.link(request.app.org, 'ris-overview'),
                attrs={'class': 'ris-settings'}
            ),
        )
    modules.links = links
    return modules


def get_api_endpoints(request: TownRequest) -> Iterator[ApiEndpoint[Any, Any]]:
    yield from get_api_endpoints_base(request)
    if request.app.org.ris_enabled:
        yield CommissionApiEndpoint(request)
        yield MeetingApiEndpoint(request)
        yield PoliticalBusinessApiEndpoint(request)
        yield ParliamentarianApiEndpoint(request)
        yield ParliamentaryGroupApiEndpoint(request)
