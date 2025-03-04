from __future__ import annotations

import uuid
import pytest

from onegov.pas.models import (
    Parliamentarian,
    ParliamentaryGroup,
    Commission,
    CommissionMembership, ParliamentarianRole,
)
from onegov.pas.importer.json_import import (
    MembershipImporter,
    PeopleImporter,
)


def test_people_importer_successful_import(session, people_json):
    importer = PeopleImporter(session)
    parliamentarian_map = importer.bulk_import(people_json['results'])

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


@pytest.fixture
def test_memberships():
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


def link_with_actual_uuids(test_memberships):
    # Generate UUIDs for the test objects
    person_1_id = str(uuid.uuid4())
    person_2_id = str(uuid.uuid4())
    commission_1_id = str(uuid.uuid4())
    commission_2_id = str(uuid.uuid4())
    fraktion_1_id = str(uuid.uuid4())
    kantonsrat_id = str(uuid.uuid4())  # Add UUID for Kantonsrat
    sonstige_1_id = str(uuid.uuid4())  # Add UUID for Sonstige-1
    sonstige_2_id = str(uuid.uuid4())  # Add UUID for Sonstige-2
    # Create mapping dictionaries to keep track of the original IDs to UUIDs
    person_id_map = {'person-1': person_1_id, 'person-2': person_2_id}
    org_id_map = {
        'commission-1': commission_1_id,
        'commission-2': commission_2_id,
        'fraktion-1': fraktion_1_id,
        'kantonsrat-1': kantonsrat_id,  # Add mapping for Kantonsrat
        'sonstige-1': sonstige_1_id,  # Add mapping for Sonstige-1
        'sonstige-2': sonstige_2_id,  # Add mapping for Sonstige-2
    }
    # Update test_memberships with the UUID values - make sure ALL references get updated
    for membership in test_memberships:
        if 'person' in membership and 'id' in membership['person']:
            person_key = membership['person']['id']
            if person_key in person_id_map:
                membership['person']['id'] = person_id_map[person_key]

        if (
            'organization' in membership
            and 'id' in membership['organization']
        ):
            org_key = membership['organization']['id']
            if org_key in org_id_map:
                membership['organization']['id'] = org_id_map[org_key]
    return (
        commission_1_id,
        commission_2_id,
        fraktion_1_id,
        kantonsrat_id,
        person_1_id,
        person_2_id,
        sonstige_1_id,
        sonstige_2_id,
    )


def test_membership_importer(session, test_memberships):
    """Test the MembershipImporter with all organization types and roles."""

    (
        commission_1_id,
        commission_2_id,
        fraktion_1_id,
        kantonsrat_id,
        person_1_id,
        person_2_id,
        sonstige_1_id,
        sonstige_2_id,
    ) = link_with_actual_uuids(test_memberships)


    # Create parliamentarians with UUIDs
    parliamentarians = {
        person_1_id: Parliamentarian(
            external_kub_id=person_1_id, first_name='John', last_name='Doe'
        ),
        person_2_id: Parliamentarian(
            external_kub_id=person_2_id,
            first_name='Jane',
            last_name='Smith',
        ),
    }

    # Create commissions with UUIDs
    commissions = {
        commission_1_id: Commission(
            external_kub_id=commission_1_id,
            name='Justizprüfungskommission (JPK)',
        ),
        commission_2_id: Commission(
            external_kub_id=commission_2_id, name='Bildungskommission'
        ),
    }

    # Create parliamentary groups with UUIDs
    parliamentary_groups = {
        fraktion_1_id: ParliamentaryGroup(
            external_kub_id=fraktion_1_id, name='CVP'
        )
    }

    # Add objects to session
    for p in parliamentarians.values():
        session.add(p)
    for c in commissions.values():
        session.add(c)
    for g in parliamentary_groups.values():
        session.add(g)
    session.flush()

    # Retrieve objects from session to get their actual IDs
    parliamentarians_db = {
        p.external_kub_id: p for p in session.query(Parliamentarian).all()
    }
    commissions_db = {
        c.external_kub_id: c for c in session.query(Commission).all()
    }
    parliamentary_groups_db = {
        g.external_kub_id: g
        for g in session.query(ParliamentaryGroup).all()
    }

    # Create the importer
    importer = MembershipImporter(session)

    # Create empty party_map and other_organization_map for the test
    party_map = {}
    other_organization_map = {}

    importer.init(
        session=session,
        parliamentarian_map=parliamentarians_db,
        commission_map=commissions_db,
        parliamentary_group_map=parliamentary_groups_db,
        party_map=party_map,
        other_organization_map=other_organization_map,
    )
    # Run the actual import
    importer.bulk_import(test_memberships)
    session.flush()

    # 1. Test Commission Memberships
    commission_memberships = session.query(CommissionMembership).all()
    assert (
        len(commission_memberships) == 2
    ), 'Expected 2 commission memberships'

    # Find president membership
    president_membership = next(
        (m for m in commission_memberships if m.role == 'president'), None
    )
    assert (
        president_membership is not None
    ), 'Commission president role not found'
    assert president_membership.parliamentarian.first_name == 'John'
    assert (
        president_membership.commission.name
        == 'Justizprüfungskommission (JPK)'
    )
    assert president_membership.start.strftime('%Y-%m-%d') == '2023-01-01'
    assert president_membership.end is None

    # Find regular member membership
    member_membership = next(
        (m for m in commission_memberships if m.role == 'member'), None
    )
    assert (
        member_membership is not None
    ), 'Commission member role not found'
    assert member_membership.parliamentarian.first_name == 'Jane'
    assert member_membership.commission.name == 'Bildungskommission'
    assert member_membership.start.strftime('%Y-%m-%d') == '2023-01-01'
    assert member_membership.end.strftime('%Y-%m-%d') == '2026-12-31'

    # 2. Test Parliamentarian Roles
    parliamentarian_roles = session.query(ParliamentarianRole).all()
    assert (
        len(parliamentarian_roles) == 5
    ), 'Expected 5 parliamentarian roles'

    # Find Kantonsrat roles
    kantonsrat_roles = [
        r
        for r in parliamentarian_roles
        if r.parliamentary_group is None
        and r.additional_information is None
    ]
    assert len(kantonsrat_roles) == 2, 'Expected 2 Kantonsrat roles'

    # Find Kantonsrat president
    kr_president = next(
        (r for r in kantonsrat_roles if r.role == 'president'), None
    )
    assert kr_president is not None, 'Kantonsrat president role not found'
    assert kr_president.parliamentarian.first_name == 'Jane'
    assert kr_president.start.strftime('%Y-%m-%d') == '2023-01-01'
    assert kr_president.end.strftime('%Y-%m-%d') == '2023-12-31'

    # Find Kantonsrat member
    kr_member = next(
        (r for r in kantonsrat_roles if r.role == 'member'), None
    )
    assert kr_member is not None, 'Kantonsrat member role not found'
    assert kr_member.parliamentarian.first_name == 'John'
    assert kr_member.start.strftime('%Y-%m-%d') == '2022-01-01'
    assert kr_member.end is None

    # 3. Test Parliamentary Group roles
    fraktion_roles = [
        r
        for r in parliamentarian_roles
        if r.parliamentary_group is not None
    ]
    assert len(fraktion_roles) == 1, 'Expected 1 parliamentary group role'
    assert fraktion_roles[0].parliamentarian.first_name == 'John'
    assert fraktion_roles[0].parliamentary_group.name == 'CVP'
    assert fraktion_roles[0].parliamentary_group_role == 'president'
    assert fraktion_roles[0].role == 'member'  # Base role is member

    # 4. Test Sonstige roles
    sonstige_roles = [
        r
        for r in parliamentarian_roles
        if r.additional_information is not None
    ]
    assert len(sonstige_roles) == 2, 'Expected 2 Sonstige roles'

    # Find Nationalrat role
    nationalrat_role = next(
        (
            r
            for r in sonstige_roles
            if 'Nationalrat' in r.additional_information
        ),
        None,
    )
    assert nationalrat_role is not None, 'Nationalrat role not found'
    assert nationalrat_role.parliamentarian.first_name == 'John'
    assert (
        'Restliche Parlamentarier'
        in nationalrat_role.additional_information
    )
    assert nationalrat_role.start.strftime('%Y-%m-%d') == '2019-01-01'

    # Find Regierungsrat role
    regierungsrat_role = next(
        (
            r
            for r in sonstige_roles
            if 'Regierungsrat' in r.additional_information
        ),
        None,
    )
    assert regierungsrat_role is not None, 'Regierungsrat role not found'
    assert regierungsrat_role.parliamentarian.first_name == 'Jane'
    assert 'Regierung' in regierungsrat_role.additional_information
    assert regierungsrat_role.start.strftime('%Y-%m-%d') == '2020-01-01'


