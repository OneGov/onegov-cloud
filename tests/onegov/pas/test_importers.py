from __future__ import annotations

import pytest

from datetime import date
from uuid import UUID

from onegov.pas.importer.json_import import (
    MembershipImporter,
    PeopleImporter,
    OrganizationImporter,
)
from onegov.pas.models import (
    PASCommission,
    PASCommissionMembership,
    PASParliamentarian,
    Party,
)
from onegov.pas.utils import is_active_kantonsrat_member


from typing import Any, cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.importer.types import MembershipData
    from sqlalchemy.orm import Session


def test_people_importer_successful_import(
    session: Session,
    people_json: dict[str, Any]
) -> None:

    importer = PeopleImporter(session)
    parliamentarian_map, details, processed_count = importer.bulk_import(
        people_json['results']
    )

    # Get sample person for detailed attribute testing
    daniel = people_json['results'][0]
    sample_parliamentarian = parliamentarian_map[daniel['id']]

    # Check basic attributes
    assert sample_parliamentarian.external_kub_id == daniel['id']
    assert sample_parliamentarian.first_name == daniel['firstName']
    assert sample_parliamentarian.last_name == daniel['officialName']
    assert sample_parliamentarian.academic_title == daniel['title']
    assert sample_parliamentarian.salutation == daniel['salutation']

    # Check email
    if daniel.get('primaryEmail'):
        assert (
            sample_parliamentarian.email_primary
            == daniel['primaryEmail']['email']
        )

    # Check all emails in bulk
    for person in people_json['results']:
        if person.get('primaryEmail'):
            parliamentarian = parliamentarian_map[person['id']]
            assert (
                parliamentarian.email_primary
                == person['primaryEmail']['email']
            )

    # Verify map contains all parliamentarians
    assert len(parliamentarian_map) == len(people_json['results'])

    # Check IDs were correctly assigned to map
    for person in people_json['results']:
        assert person['id'] in parliamentarian_map


def test_people_importer_existing_parliamentarian(
    session: Session,
    people_json: dict[str, Any]
) -> None:
    """Test importing data for a parliamentarian that already exists."""
    importer = PeopleImporter(session)

    from uuid import UUID
    # Pre-populate the database with one parliamentarian from the fixture
    existing_person_data = people_json['results'][0]
    existing_parliamentarian = PASParliamentarian(
        external_kub_id=UUID(existing_person_data['id']),  # Convert to UUID
        first_name='OldFirstName',  # Use a different first name initially
        last_name=existing_person_data['officialName'],
        salutation=existing_person_data['salutation'],
        academic_title=existing_person_data['title'],
        email_primary='old@example.org',  # Use a different email initially
    )
    session.add(existing_parliamentarian)
    session.flush()

    # Run the import with the full data, including the existing person
    parliamentarian_map, details, processed_count = importer.bulk_import(
        people_json['results']
    )

    # Verify the map contains all parliamentarians from the input
    assert len(parliamentarian_map) == len(people_json['results'])

    # Check the updated parliamentarian
    updated_parliamentarian = session.query(PASParliamentarian).filter_by(
        external_kub_id=UUID(existing_person_data['id'])  # Use UUID for query
    ).one_or_none()

    assert updated_parliamentarian is not None
    # Check that the first name was updated
    assert updated_parliamentarian.first_name == (
        existing_person_data['firstName'])
    # Check that the email was updated
    assert updated_parliamentarian.email_primary == (
        existing_person_data['primaryEmail']['email'])
    # Check other attributes remain consistent
    assert updated_parliamentarian.last_name == (
        existing_person_data['officialName'])
    assert updated_parliamentarian.salutation == (
        existing_person_data['salutation'])

    # Ensure no duplicate parliamentarian was created
    count = session.query(PASParliamentarian).filter_by(
        external_kub_id=UUID(existing_person_data['id'])  # Use UUID for query
    ).count()
    assert count == 1


def test_organization_importer_existing(
    session: Session,
    organization_json_with_fraktion: dict[str, Any]
) -> None:
    """Test importing organization data when some organizations already exist.
    """
    organization_json = organization_json_with_fraktion
    importer = OrganizationImporter(session)

    from uuid import UUID
    # Pre-populate with one of each type from the fixture
    commission_data = next(
        o
        for o in organization_json['results']
        if o['organizationTypeTitle'] == 'Kommission'
    )
    fraktion_data = next(
        o
        for o in organization_json['results']
        if o['organizationTypeTitle'] == 'Fraktion'
    )
    # Assuming 'Fraktion' maps to Party
    existing_commission = PASCommission(
        external_kub_id=UUID(commission_data['id']),  # Convert to UUID
        name='Old Commission Name',
        type='normal',
    )
    # Fraktion maps to Party
    existing_party = Party(
        external_kub_id=UUID(fraktion_data['id']),  # Convert to UUID
        name='Old Party Name',
    )
    # Add ParliamentaryGroup if needed for testing that type
    # existing_group = ParliamentaryGroup(...)

    session.add_all([existing_commission, existing_party])
    session.flush()

    # Run the import
    (
        commission_map,
        parliamentary_group_map,
        party_map,
        other_organization_map,
        details,  # Unpack details
        processed_counts,  # Unpack processed counts
    ) = importer.bulk_import(organization_json['results'])

    # --- Assertions ---

    # 1. Check Commission Update
    updated_commission = (
        session.query(PASCommission)
        .filter_by(external_kub_id=UUID(commission_data['id']))  # Use UUID
        .one_or_none()
    )
    assert updated_commission is not None
    assert (
        updated_commission.name == commission_data['name']
    )  # Check name update
    assert commission_data['id'] in commission_map
    assert commission_map[commission_data['id']] == updated_commission

    # Check Commission Count (ensure no duplicates)
    commission_count = (
        session.query(PASCommission)
        .filter_by(external_kub_id=UUID(commission_data['id']))  # Use UUID
        .count()
    )
    assert commission_count == 1

    # 2. Check Party Update (from Fraktion)
    updated_party = (
        session.query(Party)
        .filter_by(external_kub_id=UUID(fraktion_data['id']))  # Use UUID
        .one_or_none()
    )
    assert updated_party is not None
    assert updated_party.name == fraktion_data['name']  # Check name update
    assert fraktion_data['id'] in party_map  # party_map is keyed by id now
    assert party_map[fraktion_data['id']] == updated_party

    # Check Party Count (ensure no duplicates)
    party_count = (
        session.query(Party)
        .filter_by(external_kub_id=UUID(fraktion_data['id']))  # Use UUID
        .count()
    )
    assert party_count == 1


def test_membership_importer_role_transition(
    session: Session,
) -> None:
    """Same person promoted from Mitglied to Präsident in same
    commission. Both memberships must be imported — the old key
    (parliamentarian_id, commission_id) collapsed them into one."""

    from uuid import UUID

    person_kub_id = 'person-lustenberger'
    commission_kub_id = 'commission-gesundheit'

    parl = PASParliamentarian(
        first_name='Andreas',
        last_name='Lustenberger',
        external_kub_id=UUID('d6cdb745-6b69-4df7-afc0-46a81b47b8f7'),
    )
    commission = PASCommission(
        name='Kommission Gesundheit und Soziales',
        external_kub_id=UUID('a8e8fd19-d0aa-42f7-9515-22cdc26b89e3'),
    )
    session.add_all([parl, commission])
    session.flush()

    importer = MembershipImporter(session)
    importer.init(
        session=session,
        parliamentarian_map={person_kub_id: parl},
        commission_map={commission_kub_id: commission},
        parliamentary_group_map={},
        party_map={},
        other_organization_map={},
    )

    memberships_data: list[Any] = [
        {
            'id': 'membership-president',
            'organization': {
                'id': commission_kub_id,
                'name': 'Kommission Gesundheit und Soziales',
                'organizationTypeTitle': 'Kommission',
            },
            'person': {
                'id': person_kub_id,
                'firstName': 'Andreas',
                'officialName': 'Lustenberger',
                'fullName': 'Lustenberger Andreas',
                'salutation': 'Herr',
                'title': '',
                'isActive': True,
                'primaryEmail': False,
                'thirdPartyId': '58',
                'username': False,
            },
            'role': 'Präsident/-in',
            'start': '2024-07-03',
            'end': None,
            'primaryAddress': False,
            'primaryEmail': False,
        },
        {
            'id': 'membership-member',
            'organization': {
                'id': commission_kub_id,
                'name': 'Kommission Gesundheit und Soziales',
                'organizationTypeTitle': 'Kommission',
            },
            'person': {
                'id': person_kub_id,
                'firstName': 'Andreas',
                'officialName': 'Lustenberger',
                'fullName': 'Lustenberger Andreas',
                'salutation': 'Herr',
                'title': '',
                'isActive': True,
                'primaryEmail': False,
                'thirdPartyId': '58',
                'username': False,
            },
            'role': 'Mitglied',
            'start': '2024-04-15',
            'end': '2024-07-02',
            'primaryAddress': False,
            'primaryEmail': False,
        },
    ]

    importer.bulk_import(memberships_data)
    session.flush()

    cms = (
        session.query(PASCommissionMembership)
        .filter_by(parliamentarian_id=parl.id)
        .order_by(PASCommissionMembership.start)
        .all()
    )

    assert len(cms) == 2, (
        f'Expected 2 memberships, got {len(cms)}: '
        f'{[(c.role, str(c.start)) for c in cms]}'
    )

    member_cm = cms[0]
    assert member_cm.role == 'member'
    assert str(member_cm.start) == '2024-04-15'
    assert str(member_cm.end) == '2024-07-02'

    president_cm = cms[1]
    assert president_cm.role == 'president'
    assert str(president_cm.start) == '2024-07-03'
    assert president_cm.end is None


PERSON_ID = 'c3b0e5f8-2d3b-4a1c-9c3f-2f2a7b3d5e11'
COMMISSION_ID = 'e1f2a3b4-c5d6-47e8-9a0b-1c2d3e4f5a6b'
KANTONSRAT_ID = 'f0e1d2c3-b4a5-4968-8778-6a5b4c3d2e1f'


def membership_data(
    kub_id: str,
    organization: dict[str, str],
    role: str,
    start: str | None,
    end: str | None,
) -> MembershipData:
    return cast(
        'MembershipData',
        {
            'id': kub_id,
            'organization': organization,
            'person': {
                'id': PERSON_ID,
                'firstName': 'Karl',
                'officialName': 'Nussbaumer',
                'fullName': 'Nussbaumer Karl',
            },
            'role': role,
            'start': start,
            'end': end,
        },
    )


COMMISSION = {
    'id': COMMISSION_ID,
    'name': 'ad-hoc Kommission Polizeigesetz',
    'organizationTypeTitle': 'Kommission',
}

KANTONSRAT = {
    'id': KANTONSRAT_ID,
    'name': 'Kantonsrat',
    'organizationTypeTitle': 'Kantonsrat',
}


@pytest.fixture
def nussbaumer(
    session: Session,
) -> tuple[MembershipImporter, PASParliamentarian, PASCommission]:
    """A parliamentarian who returned to the Kantonsrat after a break, with
    the importer wired up for him and one commission."""
    from uuid import UUID

    parliamentarian = PASParliamentarian(
        first_name='Karl',
        last_name='Nussbaumer',
        external_kub_id=UUID(PERSON_ID),
    )
    commission = PASCommission(
        name='ad-hoc Kommission Polizeigesetz',
        external_kub_id=UUID(COMMISSION_ID),
    )
    session.add_all([parliamentarian, commission])
    session.flush()

    importer = MembershipImporter(session)
    importer.init(
        session=session,
        parliamentarian_map={PERSON_ID: parliamentarian},
        commission_map={COMMISSION_ID: commission},
        parliamentary_group_map={},
        party_map={},
        other_organization_map={},
    )
    return importer, parliamentarian, commission


def test_membership_importer_keeps_open_kantonsrat_role(
    session: Session,
    nussbaumer: tuple[MembershipImporter, PASParliamentarian, PASCommission],
) -> None:
    """A parliamentarian who left and returned holds the same role twice.
    Both periods must survive, otherwise the closed one wins and he counts
    as inactive (OGC-3263)."""

    importer, parliamentarian, _ = nussbaumer

    importer.bulk_import(
        [
            membership_data(
                '5b008748-7c0f-4c1f-9e4b-6a1e2d3c4b5a',
                KANTONSRAT,
                'Mitglied des Kantonsrates',
                '2003-01-01',
                '2020-12-17',
            ),
            membership_data(
                'ab2f351b-8d4e-4f2a-8b3c-9d0e1f2a3b4c',
                KANTONSRAT,
                'Mitglied des Kantonsrates',
                '2024-12-20',
                None,
            ),
        ]
    )
    session.flush()

    roles = sorted(parliamentarian.roles, key=lambda r: r.start or date.min)
    assert len(roles) == 2
    assert str(roles[0].start) == '2003-01-01'
    assert str(roles[0].end) == '2020-12-17'
    assert str(roles[1].start) == '2024-12-20'
    assert roles[1].end is None
    assert is_active_kantonsrat_member(parliamentarian)


def test_membership_importer_merges_duplicate_kub_memberships(
    session: Session,
    nussbaumer: tuple[MembershipImporter, PASParliamentarian, PASCommission],
) -> None:
    """KUB holds the same membership twice, under two ids. We only want one
    row for it."""

    importer, parliamentarian, _ = nussbaumer

    importer.bulk_import(
        [
            membership_data(
                '024247e5-1a2b-4c3d-8e4f-5a6b7c8d9e0f',
                COMMISSION,
                'Mitglied',
                '2026-04-30',
                None,
            ),
            membership_data(
                '46cad2bc-0f1e-4d2c-9b3a-8c7d6e5f4a3b',
                COMMISSION,
                'Mitglied',
                '2026-04-30',
                None,
            ),
        ]
    )
    session.flush()

    memberships = (
        session.query(PASCommissionMembership)
        .filter_by(parliamentarian_id=parliamentarian.id)
        .all()
    )
    assert len(memberships) == 1


def test_membership_importer_deletes_vanished_membership(
    session: Session,
    nussbaumer: tuple[MembershipImporter, PASParliamentarian, PASCommission],
) -> None:
    """A membership which is gone from KUB is removed from PAS."""

    importer, parliamentarian, commission = nussbaumer

    importer.bulk_import(
        [
            membership_data(
                '024247e5-1a2b-4c3d-8e4f-5a6b7c8d9e0f',
                COMMISSION,
                'Mitglied',
                '2026-04-30',
                None,
            ),
            membership_data(
                '5b008748-7c0f-4c1f-9e4b-6a1e2d3c4b5a',
                KANTONSRAT,
                'Mitglied des Kantonsrates',
                '2024-12-20',
                None,
            ),
        ]
    )
    session.flush()
    assert len(parliamentarian.commission_memberships) == 1
    assert len(parliamentarian.roles) == 1

    importer.bulk_import(
        [
            membership_data(
                '5b008748-7c0f-4c1f-9e4b-6a1e2d3c4b5a',
                KANTONSRAT,
                'Mitglied des Kantonsrates',
                '2024-12-20',
                None,
            ),
        ]
    )
    session.flush()
    session.expire_all()

    assert parliamentarian.commission_memberships == []
    assert len(parliamentarian.roles) == 1


def test_membership_importer_adopts_and_keeps_manual_rows(
    session: Session,
    nussbaumer: tuple[MembershipImporter, PASParliamentarian, PASCommission],
) -> None:
    """Rows imported before we stored the KUB id take over the id of their
    membership. Rows entered by hand keep an empty id and are never
    deleted."""

    importer, parliamentarian, commission = nussbaumer

    own_commission = PASCommission(name='Kommission ohne KUB')
    session.add(own_commission)
    session.flush()

    imported_before = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member',
        start=date(2026, 4, 30),
    )
    manual = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=own_commission.id,
        role='guest',
        start=date(2020, 1, 1),
    )
    session.add_all([imported_before, manual])
    session.flush()

    importer.bulk_import(
        [
            membership_data(
                '024247e5-1a2b-4c3d-8e4f-5a6b7c8d9e0f',
                COMMISSION,
                'Präsident/-in',
                '2026-04-30',
                None,
            ),
        ]
    )
    session.flush()
    session.expire_all()

    assert imported_before.external_kub_id == UUID(
        '024247e5-1a2b-4c3d-8e4f-5a6b7c8d9e0f'
    )
    assert imported_before.role == 'president'
    assert manual.external_kub_id is None
    assert len(parliamentarian.commission_memberships) == 2


@pytest.fixture
def sample_memberships() -> list[dict[str, Any]]:
    """Provide test membership data covering all organization types and
    role patterns."""
    return [
        # Kommission - Präsident
        {
            'id': 'membership-1',
            'organization': {
                'id': 'commission-1',
                'name': 'Justizprüfungskommission (JPK)',
                'organizationTypeTitle': 'Kommission',
            },
            'person': {'id': 'person-1'},
            'role': 'Präsident/-in',
            'start': '2023-01-01',
            'end': None,
        },
        # Kommission - Mitglied
        {
            'id': 'membership-2',
            'organization': {
                'id': 'commission-2',
                'name': 'Bildungskommission',
                'organizationTypeTitle': 'Kommission',
            },
            'person': {'id': 'person-2'},
            'role': 'Mitglied',
            'start': '2023-01-01',
            'end': '2026-12-31',
        },
        # Kantonsrat - Mitglied
        {
            'id': 'membership-3',
            'organization': {
                'id': 'kantonsrat-1',
                'name': 'Kantonsrat',
                'organizationTypeTitle': 'Kantonsrat',
            },
            'person': {'id': 'person-1'},
            'role': 'Mitglied des Kantonsrates',
            'start': '2022-01-01',
            'end': None,
        },
        # Kantonsrat - Präsident
        {
            'id': 'membership-4',
            'organization': {
                'id': 'kantonsrat-1',
                'name': 'Kantonsrat',
                'organizationTypeTitle': 'Kantonsrat',
            },
            'person': {'id': 'person-2'},
            'role': 'Präsident des Kantonsrates',
            'start': '2023-01-01',
            'end': '2023-12-31',
        },
        # Fraktion
        {
            'id': 'membership-5',
            'organization': {
                'id': 'fraktion-1',
                'name': 'CVP',
                'organizationTypeTitle': 'Fraktion',
            },
            'person': {'id': 'person-1'},
            'role': 'Präsident/-in',
            'start': '2023-01-01',
            'end': None,
        },
        # Sonstige - Various roles
        {
            'id': 'membership-6',
            'organization': {
                'id': 'sonstige-1',
                'name': 'Restliche Parlamentarier',
                'organizationTypeTitle': 'Sonstige',
            },
            'person': {'id': 'person-1'},
            'role': 'Nationalrat',
            'start': '2019-01-01',
            'end': None,
        },
        {
            'id': 'membership-7',
            'organization': {
                'id': 'sonstige-2',
                'name': 'Regierung',
                'organizationTypeTitle': 'Sonstige',
            },
            'person': {'id': 'person-2'},
            'role': 'Regierungsrat',
            'start': '2020-01-01',
            'end': None,
        },
    ]
