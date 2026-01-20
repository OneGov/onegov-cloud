from __future__ import annotations

import os
import transaction

from onegov.core.utils import Bunch
from onegov.org import OrgApp
from tests.shared import Client


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestOrgApp


def test_allowed_application_id(org_app: TestOrgApp) -> None:
    # little bobby tables!
    assert not org_app.is_allowed_application_id(
        "Robert'); DROP TABLE Students; --"
    )
    assert not org_app.is_allowed_application_id('foo')
    org_app.session_manager.ensure_schema_exists(org_app.namespace + '-foo')
    assert org_app.is_allowed_application_id('foo')


def test_send_email(maildir: str) -> None:

    class App(OrgApp):

        @property
        def org(self) -> Any:
            return Bunch(
                name="Gemeinde Govikon",
                title="Gemeinde Govikon",
                meta=dict(reply_to='info@govikon.ch')
            )

    app = App()
    app.mail = {
        'marketing': {
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        },
        'transactional': {
            'directory': maildir,
            'sender': 'mails@govikon.ch'
        }
    }
    app.maildir = maildir  # type: ignore[attr-defined]
    client = Client(app)

    app.send_email(
        receivers=['civilian@example.org'],
        subject='Test',
        content='Test',
        category='transactional'
    )
    assert len(os.listdir(maildir)) == 0
    transaction.abort()

    app.send_email(
        receivers=['civilian@example.org'],
        subject='Test',
        content='Test',
        category='transactional'
    )
    assert len(os.listdir(maildir)) == 0
    transaction.commit()

    assert len(os.listdir(maildir)) == 1
    mail = client.get_email(0)
    assert mail is not None
    assert mail['ReplyTo'] == 'Gemeinde Govikon <info@govikon.ch>'
    assert mail['Subject'] == 'Test'
    assert mail['From'] == 'Gemeinde Govikon <mails@govikon.ch>'


def test_cache_control_when_logged_in(client: Client[TestOrgApp]) -> None:
    resp = client.get('/')
    assert resp.headers.get('Cache-Control') != 'no-store'

    client.login_admin()
    resp = client.get('/')
    assert resp.headers.get('Cache-Control') == 'no-store'
