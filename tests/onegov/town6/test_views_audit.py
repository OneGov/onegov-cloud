from __future__ import annotations

import json
import transaction

from onegov.core.orm.audit import AUDIT_USERNAME
from onegov.page import PageCollection


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


def test_view_audit_trail(client: Client) -> None:
    session = client.app.session()
    session.info[AUDIT_USERNAME] = 'editor@example.org'
    page = PageCollection(session).add_root(
        'Audited Page',
        type='topic',
        meta={'trait': 'page'},
    )
    page.title = 'Changed Audited Page'
    session.flush()
    page_id = page.id
    transaction.commit()

    client.get('/audit-trail', status=403)
    client.login_editor()

    audit_trail = client.get('/').click('Audit Trail')
    assert 'Changed Audited Page' in audit_trail
    assert f'#{page_id}' in audit_trail
    copy_button = audit_trail.pyquery('.audit-copy')[0]
    snapshot = json.loads(copy_button.attrib['data-clipboard-text'])
    assert snapshot['id'] == page_id
    assert snapshot['title'] == 'Changed Audited Page'

    detail = audit_trail.click('Ansicht', index=0)
    assert 'Eintrag im Audit Trail' in detail
    assert '"title": "Changed Audited Page"' in detail
    assert detail.click('Changed Audited Page', index=1).status_code == 200
