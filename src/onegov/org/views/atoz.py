from __future__ import annotations

from onegov.core.security import Public
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import AtoZ


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def atoz(
    self: AtoZ[Any],
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    # FIXME: If we truly wanted this to be generic, then title should
    #        probably be a property of the AtoZ, rather than hardcoded
    layout = layout or DefaultLayout(self, request)
    assert isinstance(layout.breadcrumbs, list)
    layout.breadcrumbs.append(Link(_('Topics A-Z'), '#'))

    return {
        'title': _('Topics A-Z'),
        'model': self,
        'layout': layout
    }
