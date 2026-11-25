from __future__ import annotations

from onegov.page import PageCollection
from onegov.page.audit import page_previous_snapshot, page_snapshot


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_page_snapshot(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root('News')
    session.flush()

    snapshot = page_snapshot(root)
    assert snapshot['title'] == 'News'
    assert snapshot['file_ids'] == []


def test_page_previous_snapshot_no_changes(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root('News')
    session.flush()

    # nothing changed since the flush
    assert page_previous_snapshot(session, root) is None


def test_page_previous_snapshot_with_changes(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root('News')
    session.flush()

    # modify before flushing so the ORM history still holds the old value
    root.title = 'Latest News'
    snapshot = page_previous_snapshot(session, root)
    assert snapshot is not None
    assert snapshot['title'] == 'News'
    assert snapshot['file_ids'] == []
