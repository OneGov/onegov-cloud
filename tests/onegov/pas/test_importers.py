from __future__ import annotations

import pytest

from onegov.pas.importer.json_import import (
    PeopleImporter,
    OrganizationImporter,
)
from onegov.pas.models import (
    PASCommission,
    PASParliamentarian,
    Party,
)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
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


# FIXME: Use me or delete me
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
