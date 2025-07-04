from __future__ import annotations

from onegov.core.security import Public
from onegov.parliament.collections import PoliticalBusinessCollection
from onegov.parliament.models import PoliticalBusiness
from onegov.parliament.models.political_business import (
    POLITICAL_BUSINESS_STATUS)
from onegov.parliament.models.political_business import (
    POLITICAL_BUSINESS_TYPE)
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import PoliticalBusinessCollectionLayout
from onegov.town6.layout import PoliticalBusinessLayout

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response

    from onegov.core.types import RenderData

    from onegov.town6.request import TownRequest


@TownApp.html(
    model=PoliticalBusinessCollection,
    template='political_businesses.pt',
    permission=Public,
)
def view_political_businesses(
    self: PoliticalBusinessCollection,
    request: TownRequest,
    layout: PoliticalBusinessCollectionLayout | None = None
) -> RenderData | Response:

    return {
        # 'add_link': request.link(self, name='new'),
        'layout': layout or PoliticalBusinessCollectionLayout(self, request),
        'title': _('Political Businesses'),
        'businesses': self.batch,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
    }


@TownApp.html(
    model=PoliticalBusiness,
    template='political_business.pt',
    permission=Public,
)
def view_political_business(
    self: PoliticalBusiness,
    request: TownRequest,
) -> RenderData | Response:

    layout = PoliticalBusinessLayout(self, request)

    return {
        'layout': layout,
        'business': self,
        'title': self.title,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
        'files': getattr(self, 'files', None),
    }
