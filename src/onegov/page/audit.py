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
    data['file_ids'] = sorted(file.id for file in page.files)
    return data


def page_previous_snapshot(
    _session: Session,
    page: Page,
) -> dict[str, Any] | None:
    state = inspect(page)
    file_history = state.attrs.files.history
    column_histories = [
        state.attrs[attribute.key].history
        for attribute in state.mapper.column_attrs
    ]
    if not file_history.has_changes() and not any(
        history.has_changes() for history in column_histories
    ):
        return None

    data = {
        attribute.key: (
            history.deleted[0]
            if history.deleted
            else getattr(page, attribute.key)
        )
        for attribute, history in zip(
            state.mapper.column_attrs,
            column_histories,
            strict=True,
        )
    }
    file_ids = {file.id for file in page.files}
    file_ids.difference_update(file.id for file in file_history.added)
    file_ids.update(file.id for file in file_history.deleted)
    data['file_ids'] = sorted(file_ids)
    return data


def page_changed(session: Session, page: Page) -> bool:
    return (
        session.is_modified(page, include_collections=False)
        or inspect(page).attrs.files.history.has_changes()
    )


def page_tree_snapshot(page: Page, deleted: bool = False) -> dict[str, Any]:
    data = page_snapshot(page)
    if deleted:
        file_ids = set(data['file_ids'])
        file_ids.update(
            file.id for file in inspect(page).attrs.files.history.deleted
        )
        data['file_ids'] = sorted(file_ids)
    data['children'] = [
        page_tree_snapshot(child, deleted) for child in page.children
    ]
    return data


def page_delete_snapshot(
    session: Session,
    page: Page,
) -> dict[str, Any] | None:
    if page.parent in session.deleted:
        return None
    return page_tree_snapshot(page, deleted=True)


def register_page_auditing() -> None:
    register_audit_model(
        Page,
        snapshot=page_snapshot,
        previous_snapshot=page_previous_snapshot,
        changed=page_changed,
        delete_snapshot=page_delete_snapshot,
    )
