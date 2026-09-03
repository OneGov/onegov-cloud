from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from onegov.core.orm.audit import AuditEntry, register_audit_handlers
from onegov.page import Page, PageCollection
from onegov.page.audit import register_page_auditing


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def audit_handlers(session_manager: SessionManager) -> None:
    register_page_auditing()
    register_audit_handlers(session_manager)


def test_page_audit_entries(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user_id = uuid4().hex
    with session_manager.set_current_user(
        user_id,
        'editor@example.org',
    ):
        pages = PageCollection(session)

        root = pages.add_root('News')
        session.flush()
        root.title = 'Latest News'
        session.flush()
        root_id = root.id
        pages.delete(root)

    entries = session.query(AuditEntry).order_by(AuditEntry.created).all()

    assert [entry.operation for entry in entries] == [
        'insert',
        'update',
        'delete',
    ]
    assert all(entry.target_table == 'pages' for entry in entries)
    assert all(entry.target_id == str(root_id) for entry in entries)
    assert all(entry.user_id == user_id for entry in entries)
    assert all(entry.username == 'editor@example.org' for entry in entries)
    assert all(isinstance(entry.id, UUID) for entry in entries)
    assert entries[0].snapshot['title'] == 'News'
    assert entries[0].snapshot['file_ids'] == []
    assert entries[0].previous_snapshot == {}
    assert entries[1].previous_snapshot['title'] == 'News'
    assert entries[1].previous_snapshot['file_ids'] == []
    assert entries[1].snapshot['title'] == 'Latest News'
    assert entries[2].snapshot['title'] == 'Latest News'
    assert entries[2].previous_snapshot == {}
    assert all(entry.created is not None for entry in entries)


def test_page_audit_requires_user(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user_id = uuid4().hex
    with session_manager.set_current_user(
        user_id,
        'editor@example.org',
    ):
        with session_manager.set_current_user(None, None):
            pages = PageCollection(session)
            page = pages.add_root('News')
            session.flush()
            page.title = 'Latest News'
            session.flush()
            pages.delete(page)

    assert session.query(AuditEntry).count() == 0


def test_page_audit_retains_user_identity(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user_id = uuid4().hex
    with session_manager.set_current_user(user_id, 'old@example.org'):
        page = PageCollection(session).add_root('News')
        session.flush()

    with session_manager.set_current_user(user_id, 'new@example.org'):
        page.title = 'Latest News'
        session.flush()

    entries = session.query(AuditEntry).order_by(AuditEntry.created).all()
    assert [entry.user_id for entry in entries] == [user_id, user_id]
    assert [entry.username for entry in entries] == [
        'old@example.org',
        'new@example.org',
    ]


def test_page_audit_bulk_changes(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user_id = uuid4().hex
    with session_manager.set_current_user(
        user_id,
        'editor@example.org',
    ):
        page = PageCollection(session).add_root('News')
        session.flush()
        page_id = page.id

        session.query(Page).filter(Page.id == page_id).update(
            {'title': 'Bulk News'}
        )
        session.query(Page).filter(Page.id == page_id).delete()

    entries = session.query(AuditEntry).order_by(AuditEntry.created).all()
    assert [entry.operation for entry in entries] == [
        'insert',
        'update',
        'delete',
    ]
    assert entries[0].snapshot['title'] == 'News'
    assert entries[1].previous_snapshot['title'] == 'News'
    assert entries[1].snapshot['title'] == 'Bulk News'
    assert entries[2].snapshot['title'] == 'Bulk News'


def test_page_audit_cascaded_delete(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user_id = uuid4().hex
    with session_manager.set_current_user(
        user_id,
        'editor@example.org',
    ):
        pages = PageCollection(session)
        root = pages.add_root('Root', meta={'root': True})
        child = pages.add(
            parent=root,
            title='Child',
            content={'text': 'Child content'},
        )
        grandchild = pages.add(
            parent=child,
            title='Grandchild',
            meta={'grandchild': True},
        )
        session.flush()
        root_id = root.id
        child_id = child.id
        grandchild_id = grandchild.id

        pages.delete(root)

    entries = session.query(AuditEntry).filter_by(operation='delete').all()
    assert len(entries) == 1
    assert entries[0].target_id == str(root_id)
    assert entries[0].snapshot['title'] == 'Root'
    assert entries[0].snapshot['id'] == root_id
    assert entries[0].snapshot['meta'] == {'root': True}

    child_data = entries[0].snapshot['children'][0]
    assert child_data['title'] == 'Child'
    assert child_data['id'] == child_id
    assert child_data['parent_id'] == root_id
    assert child_data['content'] == {'text': 'Child content'}

    grandchild_data = child_data['children'][0]
    assert grandchild_data['title'] == 'Grandchild'
    assert grandchild_data['id'] == grandchild_id
    assert grandchild_data['parent_id'] == child_id
    assert grandchild_data['meta'] == {'grandchild': True}
    assert grandchild_data['children'] == []
