from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import patch

from onegov.pas.importer.json_import import (
    PeopleImporter,
    MembershipImporter
)
from onegov.pas.models import (
    Parliamentarian,
    ParliamentarianRole,
    ParliamentaryGroup,
    Commission,
    CommissionMembership
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
        assert sample_parliamentarian.email_primary ==\
               daniel['primaryEmail']['email']

    # Check all emails in bulk
    for person in people_json['results']:
        if person.get('primaryEmail'):
            parliamentarian = parliamentarian_map[person['id']]
            assert parliamentarian.email_primary == person['primaryEmail'][
                'email']

    # Verify map contains all parliamentarians
    assert len(parliamentarian_map) == len(people_json['results'])

    # Check IDs were correctly assigned to map
    for person in people_json['results']:
        assert person['id'] in parliamentarian_map



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
        assert sample_parliamentarian.email_primary ==\
               daniel['primaryEmail']['email']

    # Check all emails in bulk
    for person in people_json['results']:
        if person.get('primaryEmail'):
            parliamentarian = parliamentarian_map[person['id']]
            assert parliamentarian.email_primary == person['primaryEmail']['email']

    # Verify map contains all parliamentarians
    assert len(parliamentarian_map) == len(people_json['results'])

    # Check IDs were correctly assigned to map
    for person in people_json['results']:
        assert person['id'] in parliamentarian_map


def memberships_all_org_types():
    """Provide test membership data covering all organization types and role patterns."""
    return [
        # Kommission - Präsident
        {
            "id": "membership-1",
            "organization": {
                "id": "commission-1",
                "name": "Justizprüfungskommission (JPK)",
                "organizationTypeTitle": "Kommission"
            },
            "person": {"id": "person-1"},
            "role": "Präsident/-in",
            "start": "2023-01-01",
            "end": None
        },
        # Kommission - Mitglied
        {
            "id": "membership-2",
            "organization": {
                "id": "commission-2",
                "name": "Bildungskommission",
                "organizationTypeTitle": "Kommission"
            },
            "person": {"id": "person-2"},
            "role": "Mitglied",
            "start": "2023-01-01",
            "end": "2026-12-31"
        },
        # Kantonsrat - Mitglied
        {
            "id": "membership-3",
            "organization": {
                "id": "kantonsrat-1",
                "name": "Kantonsrat",
                "organizationTypeTitle": "Kantonsrat"
            },
            "person": {"id": "person-1"},
            "role": "Mitglied des Kantonsrates",
            "start": "2022-01-01",
            "end": None
        },
        # Kantonsrat - Präsident
        {
            "id": "membership-4",
            "organization": {
                "id": "kantonsrat-1",
                "name": "Kantonsrat",
                "organizationTypeTitle": "Kantonsrat"
            },
            "person": {"id": "person-2"},
            "role": "Präsident des Kantonsrates",
            "start": "2023-01-01",
            "end": "2023-12-31"
        },
        # Fraktion
        {
            "id": "membership-5",
            "organization": {
                "id": "fraktion-1",
                "name": "CVP",
                "organizationTypeTitle": "Fraktion"
            },
            "person": {"id": "person-1"},
            "role": "Präsident/-in",
            "start": "2023-01-01",
            "end": None
        },
        # Sonstige - Various roles
        {
            "id": "membership-6",
            "organization": {
                "id": "sonstige-1",
                "name": "Restliche Parlamentarier",
                "organizationTypeTitle": "Sonstige"
            },
            "person": {"id": "person-1"},
            "role": "Nationalrat",
            "start": "2019-01-01",
            "end": None
        },
        {
            "id": "membership-7",
            "organization": {
                "id": "sonstige-2",
                "name": "Regierung",
                "organizationTypeTitle": "Sonstige"
            },
            "person": {"id": "person-2"},
            "role": "Regierungsrat",
            "start": "2020-01-01",
            "end": None
        }
    ]


def test_membership_importer(session):
    """Test the MembershipImporter with all organization types and roles."""

    # Create test objects
    parliamentarians = {
        "person-1": Parliamentarian(external_kub_id="person-1", first_name="John", last_name="Doe"),
        "person-2": Parliamentarian(external_kub_id="person-2", first_name="Jane", last_name="Smith")
    }

    commissions = {
        "commission-1": Commission(external_kub_id="commission-1", name="Justizprüfungskommission (JPK)"),
        "commission-2": Commission(external_kub_id="commission-2", name="Bildungskommission")
    }

    parliamentary_groups = {
        "fraktion-1": ParliamentaryGroup(external_kub_id="fraktion-1", name="CVP")
    }

    # Add objects to session
    for p in parliamentarians.values():
        session.add(p)
    for c in commissions.values():
        session.add(c)
    for g in parliamentary_groups.values():
        session.add(g)
    session.flush()

    # Create the importer
    importer = MembershipImporter(session)
    importer.init(
        session=session,
        parliamentarian_map=parliamentarians,
        commission_map=commissions,
        parliamentary_group_map=parliamentary_groups
    )

    # Replace _bulk_save with a mock to inspect what would be saved
    with patch.object(importer, '_bulk_save') as mock_bulk_save:
        # Import the test memberships
        importer.bulk_import(memberships_all_org_types())

        # Should call _bulk_save twice (once for CommissionMembership, once for ParliamentarianRole)
        assert mock_bulk_save.call_count == 2

        # Get the objects that would be saved
        commission_memberships = mock_bulk_save.call_args_list[0][0][0]
        parliamentarian_roles = mock_bulk_save.call_args_list[1][0][0]

        # Verify commission memberships
        assert len(commission_memberships) == 2

        # Find the president membership
        president_membership = next(m for m in commission_memberships
                                    if m.role == 'president')
        assert president_membership.parliamentarian.id == parliamentarians["person-1"].id
        assert president_membership.commission.id == commissions["commission-1"].id
        assert president_membership.start.strftime('%Y-%m-%d') == '2023-01-01'
        assert president_membership.end is None

        # Find the regular member membership
        member_membership = next(m for m in commission_memberships
                                 if m.role == 'member')
        assert member_membership.parliamentarian.id == parliamentarians["person-2"].id
        assert member_membership.commission.id == commissions["commission-2"].id
        assert member_membership.start.strftime('%Y-%m-%d') == '2023-01-01'
        assert member_membership.end.strftime('%Y-%m-%d') == '2026-12-31'

        # Verify parliamentarian roles
        assert len(parliamentarian_roles) == 5  # 2 kantonsrat + 1 fraktion + 2 sonstige

        # Verify Kantonsrat memberships
        kantonsrat_roles = [r for r in parliamentarian_roles
                            if r.parliamentary_group is None
                            and r.additional_information is None]
        assert len(kantonsrat_roles) == 2

        # Find Kantonsrat president
        kr_president = next(r for r in kantonsrat_roles if r.role == 'president')
        assert kr_president.parliamentarian.id == parliamentarians["person-2"].id
        assert kr_president.start.strftime('%Y-%m-%d') == '2023-01-01'
        assert kr_president.end.strftime('%Y-%m-%d') == '2023-12-31'

        # Find Kantonsrat member
        kr_member = next(r for r in kantonsrat_roles if r.role == 'member')
        assert kr_member.parliamentarian.id == parliamentarians["person-1"].id
        assert kr_member.start.strftime('%Y-%m-%d') == '2022-01-01'
        assert kr_member.end is None

        # Verify Fraktion membership
        fraktion_roles = [r for r in parliamentarian_roles if r.parliamentary_group is not None]
        assert len(fraktion_roles) == 1
        assert fraktion_roles[0].parliamentarian.id == parliamentarians["person-1"].id
        assert fraktion_roles[0].parliamentary_group.id == parliamentary_groups["fraktion-1"].id
        assert fraktion_roles[0].parliamentary_group_role == 'president'
        assert fraktion_roles[0].role == 'member'  # Base role is member

        # Verify Sonstige roles
        sonstige_roles = [r for r in parliamentarian_roles if r.additional_information is not None]
        assert len(sonstige_roles) == 2

        # Find Nationalrat role
        nationalrat_role = next(r for r in sonstige_roles if "Nationalrat" in r.additional_information)
        assert nationalrat_role.parliamentarian.id == parliamentarians["person-1"].id
        assert "Restliche Parlamentarier" in nationalrat_role.additional_information
        assert nationalrat_role.start.strftime('%Y-%m-%d') == '2019-01-01'

        # Find Regierungsrat role
        regierungsrat_role = next(r for r in sonstige_roles if "Regierungsrat" in r.additional_information)
        assert regierungsrat_role.parliamentarian.id == parliamentarians["person-2"].id
        assert "Regierung" in regierungsrat_role.additional_information
        assert regierungsrat_role.start.strftime('%Y-%m-%d') == '2020-01-01'


def test_role_mapping_methods():
    """Test the role mapping helper methods."""
    importer = MembershipImporter(MagicMock())

    # Test commission role mapping
    assert importer._map_to_commission_role("Präsident/-in") == "president"
    assert importer._map_to_commission_role("Erweitertes Mitglied") == "extended_member"
    assert importer._map_to_commission_role("Gast") == "guest"
    assert importer._map_to_commission_role("Mitglied") == "member"

    # Test parliamentarian role mapping
    assert importer._map_to_parliamentarian_role("Präsident des Kantonsrates") == "president"
    assert importer._map_to_parliamentarian_role("Vizepräsident des Kantonsrates") == "vice_president"
    assert importer._map_to_parliamentarian_role("Stimmenzähler") == "vote_counter"
    assert importer._map_to_parliamentarian_role("Mitglied des Kantonsrates") == "member"

    # Test parliamentary group role mapping
    assert importer._map_to_parliamentary_group_role("Präsident/-in") == "president"
    assert importer._map_to_parliamentary_group_role("Vize-Präsident/-in") == "vice_president"
    assert importer._map_to_parliamentary_group_role("Stimmenzähler") == "vote_counter"
    assert importer._map_to_parliamentary_group_role("Mitglied") == "member"

    # Test date parsing
    assert importer._parse_date("2023-01-01") == datetime(2023, 1, 1)
    assert importer._parse_date(None) is None
    assert importer._parse_date("False") is None  # Common pattern in the API
