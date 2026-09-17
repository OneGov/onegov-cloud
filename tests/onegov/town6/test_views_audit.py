from __future__ import annotations

import json
import transaction
from uuid import uuid4

from onegov.core.orm.audit import AuditEntry
from onegov.page import Page, PageCollection


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_view_audit_trail(client: Client) -> None:
    session = client.app.session()
    page = PageCollection(session).add_root(
        'Audited Page',
        type='topic',
        meta={'trait': 'page'},
    )
    page_id = page.id
    transaction.commit()

    session = client.app.session()
    persisted_page = session.get(Page, page_id)
    assert persisted_page is not None
    user_id = uuid4().hex
    with client.app.session_manager.set_current_user(
        user_id,
        'editor@example.org',
    ):
        persisted_page.title = 'Changed Audited Page'
        session.flush()
        transaction.commit()

    client.get('/audit-trail', status=403)
    client.login_editor()
    client.get('/audit-trail', status=403)
    assert 'Audit Trail' not in client.get('/')
    client.logout()

    client.login_admin()
    audit_trail = client.get('/').click('Audit Trail')
    assert 'Changed Audited Page' in audit_trail
    assert 'Der Audit Trail zeigt, wann und von wem' in audit_trail
    assert f'#{page_id}' in audit_trail
    assert len(audit_trail.pyquery('.audit-copy')) == 0

    session = client.app.session()
    entry = (
        session.query(AuditEntry)
        .filter_by(
            target_table='pages',
            target_id=str(page_id),
            operation='update',
        )
        .one()
    )
    assert entry.user_id == user_id
    assert entry.username == 'editor@example.org'
    assert entry.previous_snapshot['title'] == 'Audited Page'
    assert entry.snapshot['title'] == 'Changed Audited Page'

    detail = audit_trail.click('Ansicht', index=0)
    assert 'Eintrag im Audit Trail' in detail
    assert 'Vor der Änderung' in detail
    assert 'Nach der Änderung' in detail
    assert len(detail.pyquery('.audit-entry-meta')) == 0
    assert detail.pyquery('.audit-entry-user').text() == 'editor@example.org'
    copy_buttons = detail.pyquery('.audit-snapshot-panel .audit-copy')
    assert len(copy_buttons) == 2
    assert copy_buttons[0].attrib['data-clipboard-target'] == (
        '#audit-previous-snapshot'
    )
    assert copy_buttons[1].attrib['data-clipboard-target'] == '#audit-snapshot'
    assert all(not button.text_content().strip() for button in copy_buttons)
    assert all(
        button.attrib['aria-label'] == 'JSON kopieren'
        for button in copy_buttons
    )
    assert (
        json.loads(detail.pyquery('#audit-previous-snapshot').text())['title']
        == 'Audited Page'
    )
    assert json.loads(detail.pyquery('#audit-snapshot').text())['title'] == (
        'Changed Audited Page'
    )
    assert len(detail.pyquery('.audit-snapshot span')) == 0
    assert detail.click('Changed Audited Page', index=1).status_code == 200


def test_audit_trail_shows_deleted_subpage_count(client: Client) -> None:
    session = client.app.session()
    pages = PageCollection(session)
    root = pages.add_root('Root page', type='topic')
    child = pages.add(parent=root, title='Child page', type='topic')
    pages.add(parent=child, title='Grandchild page', type='topic')
    root_id = root.id
    transaction.commit()

    session = client.app.session()
    persisted_root = session.get(Page, root_id)
    assert persisted_root is not None
    with client.app.session_manager.set_current_user(
        uuid4().hex,
        'admin@example.org',
    ):
        PageCollection(session).delete(persisted_root)
        transaction.commit()

    client.login_admin()
    audit_trail = client.get('/audit-trail')
    facts = audit_trail.pyquery('.audit-entry-fact')
    assert len(facts) == 1
    assert 'Enthaltene Unterseiten' in facts[0].text_content()
    assert facts[0].text_content().strip().endswith(': 2')


def test_audit_trail_records_page_description_update(client: Client) -> None:
    session = client.app.session()
    page = PageCollection(session).add_root(
        'Audited Page',
        type='topic',
        meta={'trait': 'page'},
        content={'lead': 'Original description'},
    )
    page_id = page.id
    transaction.commit()

    client.login_admin()
    edit_page = client.get(f'/editor/edit/page/{page_id}')
    edit_page.form['lead'] = 'Updated description'
    edit_page.form.submit().follow()

    session = client.app.session()
    entry = (
        session.query(AuditEntry)
        .filter_by(
            target_table='pages',
            target_id=str(page_id),
            operation='update',
        )
        .one()
    )
    assert entry.snapshot['content']['lead'] == 'Updated description'
