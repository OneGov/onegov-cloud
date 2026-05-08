from __future__ import annotations

import json

from webtest import Upload
from onegov.pas.models import PASParliamentarian

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import Client, ExtendedResponse
    from .conftest import TestPasApp


PERSON_ID = 'bb440b57-0275-4d7b-a58d-1378612f9c27'
KANTONSRAT_ORG_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
BUERO_ORG_ID = 'f9e8d7c6-b5a4-3210-fedc-ba0987654321'


def _people_json() -> dict[str, Any]:
    return {
        'results': [
            {
                'created': '2024-12-23T16:44:12.056040+01:00',
                'firstName': 'Erika',
                'fullName': 'Muster Erika',
                'id': PERSON_ID,
                'isActive': True,
                'modified': '2024-12-23T16:44:12.056046+01:00',
                'officialName': 'Muster',
                'personTypeTitle': None,
                'primaryEmail': {
                    'id': 'c28dbad1-99fd-4694-8816-9c1bbd3dec72',
                    'label': '1. E-Mail',
                    'email': 'erika.muster@example.org',
                    'isDefault': True,
                    'thirdPartyId': None,
                    'modified': '2024-12-23T16:44:12.059162+01:00',
                    'created': '2024-12-23T16:44:12.059150+01:00',
                },
                'salutation': 'Frau',
                'tags': [],
                'thirdPartyId': '42',
                'title': '',
                'username': None,
            },
        ],
    }


def _organization_json() -> dict[str, Any]:
    return {
        'results': [
            {
                'created': '2024-12-23T16:44:24.920938+01:00',
                'description': '',
                'id': KANTONSRAT_ORG_ID,
                'isActive': True,
                'memberCount': 80,
                'modified': '2025-01-06T10:19:49.765454+01:00',
                'name': 'Kantonsrat',
                'organizationTypeTitle': 'Kantonsrat',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
            {
                'created': '2024-12-23T16:44:24.928269+01:00',
                'description': '',
                'id': BUERO_ORG_ID,
                'isActive': True,
                'memberCount': 10,
                'modified': '2025-01-06T10:19:54.708568+01:00',
                'name': 'Büro des Kantonsrats',
                'organizationTypeTitle': 'Kommission',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
        ],
    }


def _memberships_json() -> dict[str, Any]:
    person_block = {
        'created': '2024-12-23T16:44:12.056040+01:00',
        'firstName': 'Erika',
        'fullName': 'Muster Erika',
        'id': PERSON_ID,
        'isActive': True,
        'modified': '2024-12-23T16:44:12.056046+01:00',
        'officialName': 'Muster',
        'personTypeTitle': None,
        'primaryEmail': {
            'id': 'c28dbad1-99fd-4694-8816-9c1bbd3dec72',
            'label': '1. E-Mail',
            'email': 'erika.muster@example.org',
            'isDefault': True,
            'thirdPartyId': False,
            'modified': '2024-12-23T16:44:12.059162+01:00',
            'created': '2024-12-23T16:44:12.059150+01:00',
        },
        'salutation': 'Frau',
        'tags': [],
        'thirdPartyId': '42',
        'title': '',
        'username': False,
    }
    return {
        'results': [
            {
                'department': '',
                'description': '',
                'emailReceptionType': 'to',
                'end': False,
                'id': '11111111-1111-1111-1111-111111111111',
                'isDefault': True,
                'organization': {
                    'created': '2024-12-23T16:44:24.920938+01:00',
                    'description': '',
                    'id': KANTONSRAT_ORG_ID,
                    'isActive': True,
                    'memberCount': 80,
                    'modified': '2025-01-06T10:19:49.765454+01:00',
                    'name': 'Kantonsrat',
                    'organizationTypeTitle': 'Kantonsrat',
                    'primaryEmail': False,
                    'status': 1,
                    'thirdPartyId': False,
                    'organizationType': 1,
                    'primaryAddress': False,
                    'primaryPhoneNumber': False,
                    'primaryUrl': False,
                    'statusDisplay': 'Aktiv',
                    'tags': [],
                    'type': 'organization',
                },
                'person': person_block,
                'primaryAddress': False,
                'primaryEmail': False,
                'primaryPhoneNumber': False,
                'primaryUrl': False,
                'email': False,
                'phoneNumber': False,
                'address': False,
                'urlField': False,
                'role': 'Vize-Präsidentin',
                'start': '2024-12-20',
                'text': 'Muster Erika - Kantonsrat (Vize-Präsidentin)',
                'thirdPartyId': False,
                'type': 'membership',
                'typedId': (
                    'membership:11111111-1111-1111-1111-111111111111'
                ),
            },
            {
                'department': '',
                'description': '',
                'emailReceptionType': 'to',
                'end': False,
                'id': '22222222-2222-2222-2222-222222222222',
                'isDefault': True,
                'organization': {
                    'created': '2024-12-23T16:44:24.928269+01:00',
                    'description': '',
                    'id': BUERO_ORG_ID,
                    'isActive': True,
                    'memberCount': 10,
                    'modified': '2025-01-06T10:19:54.708568+01:00',
                    'name': 'Büro des Kantonsrats',
                    'organizationTypeTitle': 'Kommission',
                    'primaryEmail': False,
                    'status': 1,
                    'thirdPartyId': False,
                    'organizationType': 3,
                    'primaryAddress': False,
                    'primaryPhoneNumber': False,
                    'primaryUrl': False,
                    'statusDisplay': 'Aktiv',
                    'tags': [],
                    'type': 'organization',
                },
                'person': person_block,
                'primaryAddress': False,
                'primaryEmail': False,
                'primaryPhoneNumber': False,
                'primaryUrl': False,
                'email': False,
                'phoneNumber': False,
                'address': False,
                'urlField': False,
                'role': 'Vize-Präsidentin',
                'start': '2024-12-20',
                'text': (
                    'Muster Erika - Büro des Kantonsrats '
                    '(Vize-Präsidentin)'
                ),
                'thirdPartyId': False,
                'type': 'membership',
                'typedId': (
                    'membership:22222222-2222-2222-2222-222222222222'
                ),
            },
        ],
    }


def _upload(filename: str, data: dict[str, Any]) -> Upload:
    return Upload(
        filename,
        json.dumps(data).encode('utf-8'),
        'application/json',
    )


def _do_import(
    client: Client[TestPasApp],
) -> ExtendedResponse:
    page = client.get('/pas-import')
    page.form['validate_schema'] = False
    page.form['organizations_source'] = [
        _upload('organizations.json', _organization_json())
    ]
    page.form['memberships_source'] = [
        _upload('memberships.json', _memberships_json())
    ]
    page.form['people_source'] = [
        _upload('people.json', _people_json())
    ]
    result = page.form.submit().maybe_follow()
    assert result.status_code == 200, f'Import failed: {result.text}'
    return result


def test_vice_president_not_mapped_as_president(
    client: Client[TestPasApp],
) -> None:
    """Vize-Präsidentin must not be mapped to president.

    Bug: 'präsident' in role_text matched 'Vize-Präsidentin' because
    it is a substring. Fix: check vizepräsident before präsident.
    """
    client.login_admin()
    _do_import(client)

    session = client.app.session()
    erika = session.query(PASParliamentarian).filter_by(
        email_primary='erika.muster@example.org'
    ).first()
    assert erika is not None

    # Kantonsrat role: must be vice_president, not president
    role_values = [r.role for r in erika.roles]
    assert 'vice_president' in role_values, (
        f'Expected vice_president in roles, got {role_values}'
    )
    assert 'president' not in role_values, (
        f'president should not appear in roles, got {role_values}'
    )

    # Büro des Kantonsrats (Kommission): must be member, not president
    commission_roles = {
        cm.commission.name: cm.role
        for cm in erika.commission_memberships
    }
    assert commission_roles.get('Büro des Kantonsrats') == 'member', (
        f'Büro commission role should be member, '
        f'got {commission_roles}'
    )
