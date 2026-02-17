from __future__ import annotations

import transaction

from onegov.org.models.external_link import (
    ExternalFormLink, ExternalResourceLink)
from onegov.org.models.meeting import Meeting
from onegov.org.models.parliament import (
    RISCommission, RISParliamentarian, RISParliamentaryGroup)
from onegov.org.models.political_business import PoliticalBusiness
from onegov.people import Person
from sedate import utcnow

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client, TestTownApp


def test_api_lists_new_endpoints(client: Client) -> None:
    response = client.get('/api')
    assert response.status_code == 200

    data = response.json
    queries = data['collection']['queries']
    endpoint_names = [q['data'][0]['value'] for q in queries]

    assert 'forms' in endpoint_names
    assert 'resources' in endpoint_names
    assert 'people' in endpoint_names
    assert 'meetings' in endpoint_names
    assert 'political_businesses' in endpoint_names
    assert 'parliamentarians' in endpoint_names
    assert 'commissions' in endpoint_names
    assert 'parliamentary_groups' in endpoint_names


def test_api_people_endpoint(client: Client, town_app: TestTownApp) -> None:
    session = town_app.session()
    session.add(Person(
        first_name='Hans',
        last_name='Muster',
        function='Mayor',
        email='hans@example.org',
        phone='0791234567',
        phone_direct='0791234568',
        organisation='Town Hall',
        academic_title='Dr.',
        profession='Politician',
        salutation='Herr',
        political_party='FDP',
    ))
    transaction.commit()

    response = client.get('/api/people')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['first_name'] == 'Hans'
    assert item_data['last_name'] == 'Muster'
    assert item_data['function'] == 'Mayor'
    assert item_data['email'] == 'hans@example.org'
    assert item_data['phone'] == '0791234567'
    assert item_data['phone_direct'] == '0791234568'
    assert item_data['organisation'] == 'Town Hall'
    assert item_data['academic_title'] == 'Dr.'
    assert item_data['profession'] == 'Politician'
    assert item_data['salutation'] == 'Herr'
    assert item_data['political_party'] == 'FDP'
    assert 'modified' in item_data


def test_api_meetings_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    now = utcnow()
    session.add(Meeting(
        title='Council Meeting',
        start_datetime=now,
        address='Town Hall, Main Street 1',
    ))
    transaction.commit()

    response = client.get('/api/meetings')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['title'] == 'Council Meeting'
    assert item_data['start_datetime'] is not None
    assert 'Town Hall' in (item_data['address'] or '')


def test_api_political_businesses_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(PoliticalBusiness(
        title='Motion about parks',
        number='2024.001',
        political_business_type='motion',
        status='pendent_legislative',
    ))
    transaction.commit()

    response = client.get('/api/political_businesses')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['title'] == 'Motion about parks'
    assert item_data['number'] == '2024.001'
    assert item_data['political_business_type'] == 'motion'
    assert item_data['status'] == 'pendent_legislative'
    assert item_data['display_name'] == '2024.001 Motion about parks'


def test_api_parliamentarians_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(RISParliamentarian(
        first_name='Anna',
        last_name='Mueller',
        party='SP',
    ))
    transaction.commit()

    response = client.get('/api/parliamentarians')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['first_name'] == 'Anna'
    assert item_data['last_name'] == 'Mueller'
    assert item_data['party'] == 'SP'


def test_api_commissions_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(RISCommission(name='Finance Commission'))
    transaction.commit()

    response = client.get('/api/commissions')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['name'] == 'Finance Commission'


def test_api_parliamentary_groups_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(RISParliamentaryGroup(name='Green Party Group'))
    transaction.commit()

    response = client.get('/api/parliamentary_groups')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['name'] == 'Green Party Group'


def test_api_forms_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    response = client.get('/api/forms')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) >= 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['type'] == 'internal'
    assert 'title' in item_data
    assert 'text' in item_data


def test_api_forms_with_external_links(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(ExternalFormLink(
        title='External Survey',
        url='https://example.org/survey',
        group='Surveys',
    ))
    transaction.commit()

    response = client.get('/api/forms')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']

    external_items = [
        item for item in items
        if any(d['name'] == 'type' and d['value'] == 'external'
               for d in item['data'])
    ]
    assert len(external_items) == 1

    ext_data = {d['name']: d['value'] for d in external_items[0]['data']}
    assert ext_data['title'] == 'External Survey'
    assert ext_data['url'] == 'https://example.org/survey'
    assert ext_data['group'] == 'Surveys'


def test_api_resources_endpoint(
    client: Client, town_app: TestTownApp
) -> None:
    response = client.get('/api/resources')
    assert response.status_code == 200
    data = response.json
    assert 'items' in data['collection']


def test_api_resources_with_external_links(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(ExternalResourceLink(
        title='External Room',
        url='https://example.org/room',
        group='Rooms',
    ))
    transaction.commit()

    response = client.get('/api/resources')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']

    external_items = [
        item for item in items
        if any(d['name'] == 'kind' and d['value'] == 'external'
               for d in item['data'])
    ]
    assert len(external_items) == 1

    ext_data = {d['name']: d['value'] for d in external_items[0]['data']}
    assert ext_data['title'] == 'External Room'
    assert ext_data['url'] == 'https://example.org/room'
