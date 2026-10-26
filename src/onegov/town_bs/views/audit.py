from onegov.core.orm.audit import AuditEntry, AuditEntryCollection
from onegov.core.security import Secret
from onegov.org.views.audit import view_audit_entry, view_audit_trail
from onegov.town_bs import TownBsApp
from onegov.town6.layout import AuditTrailLayout


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownBsApp.html(
    model=AuditEntryCollection,
    template='audit_trail.pt',
    permission=Secret,
)
def town_bs_view_audit_trail(
    self: AuditEntryCollection,
    request: TownRequest,
) -> RenderData:
    return view_audit_trail(
        self,
        request,
        AuditTrailLayout(self, request),
    )


@TownBsApp.html(
    model=AuditEntry,
    template='audit_entry.pt',
    permission=Secret,
)
def town_bs_view_audit_entry(
    self: AuditEntry,
    request: TownRequest,
) -> RenderData:
    return view_audit_entry(
        self,
        request,
        AuditTrailLayout(self, request),
    )
