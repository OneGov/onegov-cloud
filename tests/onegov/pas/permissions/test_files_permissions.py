from __future__ import annotations

import re
import transaction

from webtest import Upload

from onegov.pas.collections import (
    PASCommissionCollection,
    PASParliamentarianCollection,
)
from onegov.pas.models import PASCommissionMembership
from onegov.user import UserCollection


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.shared.client import Client
    from ..conftest import TestPasApp


def test_commission_president_can_access_files(
    client: 'Client[TestPasApp]',
) -> None:
    session = client.app.session()

    client.login_admin()
    page = client.get('/files')
    page.form['file'] = [Upload('test.pdf', b'pdfcontent', 'application/pdf')]
    page.form.submit()

    page = client.get('/files')
    match = re.search(r'/storage/([^/]+)/details', page.text)
    assert match, 'No file found on /files page'
    file_id = match.group(1)

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='Paula',
        last_name='President',
        email_primary='paula.president@example.org',
        zg_username='zgpaula',
    )
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')
    session.add(
        PASCommissionMembership(
            parliamentarian_id=parl.id,
            commission_id=commission.id,
            role='president',
        )
    )
    users = UserCollection(session)
    user = users.by_username('zgpaula')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'
    transaction.commit()

    client.login('zgpaula', 'test')

    assert client.get('/files').status_int == 200
    assert (client.get(f'/storage/{file_id}/details').status_int
        == 200
    )
