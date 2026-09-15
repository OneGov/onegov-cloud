from __future__ import annotations

import pytest

from depot.manager import DepotManager
from onegov.core.custom import json
from onegov.file import File
from onegov.page import Page, PageCollection
from onegov.page.audit import page_snapshot, page_tree_snapshot
from onegov.page.restore import PageRestore


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session


@pytest.fixture
def depot(temporary_directory: str) -> Iterator[None]:
    DepotManager.configure(
        'default',
        {
            'depot.backend': 'depot.io.local.LocalFileStorage',
            'depot.storage_path': temporary_directory,
        },
    )
    yield
    DepotManager._clear()  # type: ignore[attr-defined]


@pytest.mark.usefixtures('depot')
def test_restore_deleted_tree(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root('Root', meta={'access': 'private'})
    child = pages.add(root, 'Child', content={'text': 'Original'})
    file = File(name='readme.txt', reference=b'README')
    child.files.append(file)
    session.flush()
    snapshot = json.loads(json.dumps(page_tree_snapshot(root)))
    pages.delete(root)
    session.flush()
    session.expunge_all()

    restored = PageRestore.prepare(session, snapshot).apply(session)
    session.expire_all()
    assert page_tree_snapshot(restored) == snapshot
    assert restored.children[0].files[0].reference.file.read() == b'README'


def test_restore_existing_page(session: Session) -> None:
    pages = PageCollection(session)
    page = pages.add_root('Original', content={'text': 'Original'})
    session.flush()
    snapshot = page_snapshot(page)
    page.title = 'Changed'
    page.content = {'text': 'Changed'}
    child = pages.add(page, 'New child')
    session.flush()

    PageRestore.prepare(session, snapshot).apply(session)
    session.expire_all()
    assert page_snapshot(page) == snapshot
    assert page.children == [child]


def test_restore_missing_files(session: Session) -> None:
    page = PageCollection(session).add_root('Original')
    session.flush()
    snapshot = page_snapshot(page)
    snapshot['file_ids'] = ['missing-file']
    snapshot['title'] = 'Restored'
    with pytest.raises(ValueError, match='Missing files: missing-file'):
        PageRestore.prepare(session, snapshot)
    assert page.title == 'Original'
    plan = PageRestore.prepare(session, snapshot, skip_missing_files=True)
    assert plan.missing_files == ['missing-file']
    plan.apply(session)
    assert page.title == 'Restored'
    assert page.files == []


@pytest.mark.parametrize('problem', ['parent', 'cycle', 'name', 'duplicate'])
def test_restore_invalid_tree(session: Session, problem: str) -> None:
    pages = PageCollection(session)
    root = pages.add_root('Root')
    child = pages.add(root, 'Child')
    session.flush()
    snapshot = page_tree_snapshot(root)
    if problem == 'parent':
        snapshot['parent_id'] = 999999
    elif problem == 'cycle':
        snapshot['parent_id'] = child.id
    elif problem == 'name':
        other = pages.add_root('Other')
        session.flush()
        snapshot['name'] = other.name
    else:
        snapshot['children'].append(snapshot['children'][0])
    with pytest.raises(ValueError):
        PageRestore.prepare(session, snapshot)
    assert session.get(Page, root.id) is root
    assert root.parent is None


def test_restore_moved_page(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root('Root')
    other = pages.add_root('Other')
    page = pages.add(root, 'Bravo')
    pages.add(root, 'Alpha')
    pages.add(root, 'Charlie')
    session.flush()
    snapshot = page_snapshot(page)
    page.parent = other
    page.title = 'Zulu'
    session.flush()

    PageRestore.prepare(session, snapshot).apply(session)
    session.expire_all()
    assert page_snapshot(page) == snapshot
    assert page.parent == root
