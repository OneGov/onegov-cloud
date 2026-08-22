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
    assert f'#{page_id}' in audit_trail
    copy_button = audit_trail.pyquery('.audit-copy')[0]
    snapshot = json.loads(copy_button.attrib['data-clipboard-text'])
    assert snapshot['id'] == page_id
    assert snapshot['title'] == 'Changed Audited Page'

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
    assert '"title": "Audited Page"' in detail
    assert '"title": "Changed Audited Page"' in detail
    assert detail.click('Changed Audited Page', index=1).status_code == 200
