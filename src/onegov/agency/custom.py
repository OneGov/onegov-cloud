from __future__ import annotations

from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.core.elements import Link
from onegov.core.utils import Bunch
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.town6.layout import DefaultLayout
from onegov.org.models import Organisation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.agency.request import AgencyRequest
    from onegov.core.elements import LinkGroup
    from onegov.town6.layout import NavigationEntry


def get_global_tools(request: AgencyRequest) -> Iterator[Link | LinkGroup]:
    for item in get_global_tools_base(request):
        title = getattr(item, 'title', None)

        if title == 'Management':
            assert isinstance(item.links, list)
            item.links.append(Link(
                text=_('Hidden contents'),
                url=request.class_link(Organisation, name='view-hidden'),
                attrs={'class': 'hidden-contents'}
            ))

        yield item


def get_top_navigation(request: AgencyRequest) -> Iterator[NavigationEntry]:
    yield (
        Bunch(id=-2, access='public', published=True),
        Link(  # type:ignore[misc]
            text=_('People'),
            url=request.class_link(ExtendedPersonCollection)
        ),
        ()
    )
    yield (
        Bunch(id=-1, access='public', published=True),
        Link(  # type:ignore[misc]
            text=_('Agencies'),
            url=request.class_link(ExtendedAgencyCollection)
        ),
        ()
    )
    yield from DefaultLayout(request.app.org, request).top_navigation or ()
