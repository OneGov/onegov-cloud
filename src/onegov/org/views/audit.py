from __future__ import annotations

from onegov.core.custom import json
from onegov.core.elements import Link
from onegov.core.orm.audit import AuditEntry, AuditEntryCollection
from onegov.core.security import Secret
from onegov.org import _, OrgApp
from onegov.org.layout import AuditTrailLayout
from onegov.page import Page


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(
    model=AuditEntryCollection,
    template='audit_trail.pt',
    permission=Secret,
)
def view_audit_trail(
    self: AuditEntryCollection,
    request: OrgRequest,
    layout: AuditTrailLayout | None = None,
) -> RenderData:
    entries = self.batch
    filters = [
        Link(
            text=request.translate(_('All')),
            active=self.operation is None,
            url=request.link(self.for_operation(None)),
        ),
        Link(
            text=request.translate(_('Created')),
            active=self.operation == 'insert',
            url=request.link(self.for_operation('insert')),
        ),
        Link(
            text=request.translate(_('Changed')),
            active=self.operation == 'update',
            url=request.link(self.for_operation('update')),
        ),
        Link(
            text=request.translate(_('Deleted')),
            active=self.operation == 'delete',
            url=request.link(self.for_operation('delete')),
        ),
    ]
    return {
        'layout': layout or AuditTrailLayout(self, request),
        'title': _('Audit Trail'),
        'entries': entries,
        'filters': filters,
        'snapshots': {
            entry.id: json.dumps(entry.snapshot, indent=2) for entry in entries
        },
    }


@OrgApp.html(
    model=AuditEntry,
    template='audit_entry.pt',
    permission=Secret,
)
def view_audit_entry(
    self: AuditEntry,
    request: OrgRequest,
    layout: AuditTrailLayout | None = None,
) -> RenderData:
    layout = layout or AuditTrailLayout(self, request)
    layout.breadcrumbs.append(Link(str(self.id), request.link(self)))
    current_page = None
    if self.target_table == 'pages' and self.target_id.isdigit():
        current_page = request.session.get(Page, int(self.target_id))
    operation = request.translate(
        {
            'insert': _('Created'),
            'update': _('Changed'),
            'delete': _('Deleted'),
        }.get(self.operation, self.operation)
    )

    return {
        'layout': layout,
        'title': _('Audit Trail Entry'),
        'entry': self,
        'operation': operation,
        'current_page': current_page,
        'snapshot': json.dumps(self.snapshot, indent=2),
        'previous_snapshot': (
            json.dumps(self.previous_snapshot, indent=2)
            if self.previous_snapshot
            else None
        ),
    }
