from __future__ import annotations

from onegov.core.custom import json
from onegov.core.elements import Link
from onegov.core.orm.audit import AuditEntry, AuditEntryCollection
from onegov.core.security import Secret
from onegov.org import _, OrgApp
from onegov.org.layout import AuditTrailLayout
from onegov.page import Page


from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


class AuditEntryFact(NamedTuple):
    label: str
    value: object


def page_snapshot_subpage_count(
    snapshot: dict[str, object],
) -> int | None:
    children = snapshot.get('children')
    if not isinstance(children, list):
        return None

    count = 0
    remaining = children.copy()
    while remaining:
        child = remaining.pop()
        if not isinstance(child, dict):
            continue
        count += 1
        grandchildren = child.get('children')
        if isinstance(grandchildren, list):
            remaining.extend(grandchildren)
    return count


def page_audit_entry_facts(
    entry: AuditEntry,
    request: OrgRequest,
) -> tuple[AuditEntryFact, ...]:
    count = page_snapshot_subpage_count(entry.snapshot)
    if count is None:
        return ()
    return (
        AuditEntryFact(
            request.translate(_('Contained subpages')),
            count,
        ),
    )


AUDIT_ENTRY_FACTORIES: dict[
    str,
    Callable[[AuditEntry, OrgRequest], tuple[AuditEntryFact, ...]],
] = {
    'pages': page_audit_entry_facts,
}


def audit_entry_facts(
    entry: AuditEntry,
    request: OrgRequest,
) -> tuple[AuditEntryFact, ...]:
    factory = AUDIT_ENTRY_FACTORIES.get(entry.target_table)
    return factory(entry, request) if factory else ()


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
        'entry_facts': {
            entry.id: audit_entry_facts(entry, request) for entry in entries
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
