from __future__ import annotations

from onegov.core.security import Private
from onegov.org.models import GeneralFileCollection
from onegov.org.views.files import view_get_file_collection
from onegov.pas import PasApp
from onegov.town6.layout import GeneralFileCollectionLayout


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=GeneralFileCollection, template='files.pt', permission=Private
)
def pas_view_file_collection(
    self: GeneralFileCollection, request: TownRequest
) -> RenderData:
    request.include('custom')
    return view_get_file_collection(
        self, request, GeneralFileCollectionLayout(self, request)
    )
