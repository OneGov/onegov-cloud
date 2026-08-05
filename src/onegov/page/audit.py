from __future__ import annotations

from onegov.core.orm.audit import register_audit_model
from onegov.page.model import Page
from sqlalchemy import inspect


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def page_snapshot(page: Page) -> dict[str, Any]:
    state = inspect(page)
    data = {
        attribute.key: getattr(page, attribute.key)
        for attribute in state.mapper.column_attrs
    }
    file_ids = {file.id for file in page.files}
    file_ids.update(file.id for file in state.attrs.files.history.deleted)
    file_ids.update(state.info.get('audit_file_ids', ()))
    data['file_ids'] = sorted(file_ids)
    return data


def prepare_page_delete_audit(page: Page) -> None:
    state = inspect(page)
    state.info['audit_deleting'] = True
    state.info['audit_file_ids'] = tuple(file.id for file in page.files)


def page_changed(session: Session, page: Page) -> bool:
    if inspect(page).info.get('audit_deleting'):
        return False
    return (
        session.is_modified(page, include_collections=False)
        or inspect(page).attrs.files.history.has_changes()
    )


def page_tree_snapshot(page: Page) -> dict[str, Any]:
    data = page_snapshot(page)
    data['children'] = [page_tree_snapshot(child) for child in page.children]
    return data


def page_delete_snapshot(
    session: Session,
    page: Page,
) -> dict[str, Any] | None:
    if page.parent in session.deleted:
        return None
    return page_tree_snapshot(page)


register_audit_model(
    Page,
    snapshot=page_snapshot,
    changed=page_changed,
    delete_snapshot=page_delete_snapshot,
)
