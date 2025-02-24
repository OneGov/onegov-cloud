from __future__ import annotations

from onegov.pas.importer.json_import import (
    PeopleImporter,
    OrganizationImporter,
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


def test_organizations_importer(session, organization_json):
    importer = OrganizationImporter(session)
