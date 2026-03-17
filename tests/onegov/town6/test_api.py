from __future__ import annotations

from datetime import timedelta

import transaction

from onegov.form import FormCollection
from onegov.org.models.external_link import (
    ExternalFormLink, ExternalResourceLink)
from onegov.org.models.meeting import Meeting
from onegov.org.models.parliament import (
    RISCommission, RISParliamentarian, RISParliamentaryGroup)
from onegov.org.models.political_business import PoliticalBusiness
from onegov.people import Person
from onegov.reservation import ResourceCollection
from sedate import utcnow

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client, TestTownApp


def api_item_data(item: dict[str, Any]) -> dict[str, Any]:
    return {
        entry['name']: entry['value']
        for entry in item['data']
    }


def api_items(
    client: Client,
    url: str,
    page: int | None = None,
) -> list[dict[str, Any]]:
    page_param = '' if page is None else f'?page={page}'
    response = client.get(f'{url}{page_param}')
    assert response.status_code == 200
    return response.json['collection']['items']


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

    item_data = api_item_data(items[0])
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

    item_data = api_item_data(items[0])
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

    item_data = api_item_data(items[0])
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

    item_data = api_item_data(items[0])
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

    item_data = api_item_data(items[0])
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

    item_data = api_item_data(items[0])
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

    ext_data = api_item_data(external_items[0])
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

    ext_data = api_item_data(external_items[0])
    assert ext_data['title'] == 'External Room'
    assert ext_data['url'] == 'https://example.org/room'


def test_api_forms_paginates_external_links_and_hides_invisible_items(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    forms = FormCollection(session)

    for ix in range(25):
        form = forms.definitions.add(
            f'API Form {ix:02d}',
            'E-Mail *= @@@',
            type='custom',
        )
        form.access = 'public'  # type:ignore[attr-defined]

    hidden_form = forms.definitions.add(
        'API Form Hidden',
        'E-Mail *= @@@',
        type='custom',
    )
    hidden_form.access = 'private'  # type:ignore[attr-defined]

    session.add(ExternalFormLink(
        title='API External Form',
        url='https://example.org/forms/public',
        group='API',
    ))
    hidden_external = ExternalFormLink(
        title='API External Hidden',
        url='https://example.org/forms/private',
        group='API',
    )
    hidden_external.access = 'private'
    session.add(hidden_external)
    transaction.commit()

    pages = [api_items(client, '/api/forms', page) for page in range(5)]
    relevant = [
        api_item_data(item)['title']
        for items in pages
        for item in items
        if str(api_item_data(item)['title']).startswith('API ')
    ]

    assert all(len(items) <= 25 for items in pages)
    assert relevant.count('API External Form') == 1
    assert 'API External Hidden' not in relevant
    assert 'API Form Hidden' not in relevant
    assert len(set(relevant)) == 26

    client.get(f'/api/forms/{hidden_form.id}', status=404)
    client.get(f'/api/forms/{hidden_external.id.hex}', status=404)


def test_api_resources_paginates_external_links_and_hides_invisible_items(
    client: Client, town_app: TestTownApp
) -> None:
    resources = ResourceCollection(town_app.libres_context)

    for ix in range(25):
        resources.add(
            title=f'API Resource {ix:02d}',
            timezone='Europe/Zurich',
            type='room',
            meta={'access': 'public'},
        )

    hidden_resource = resources.add(
        title='API Resource Hidden',
        timezone='Europe/Zurich',
        type='room',
        meta={'access': 'private'},
    )

    session = town_app.session()
    session.add(ExternalResourceLink(
        title='API External Resource',
        url='https://example.org/resources/public',
        group='API',
    ))
    hidden_external = ExternalResourceLink(
        title='API External Resource Hidden',
        url='https://example.org/resources/private',
        group='API',
    )
    hidden_external.access = 'private'
    session.add(hidden_external)
    transaction.commit()

    pages = [api_items(client, '/api/resources', page) for page in range(5)]
    relevant = [
        api_item_data(item)['title']
        for items in pages
        for item in items
        if str(api_item_data(item)['title']).startswith('API ')
    ]

    assert all(len(items) <= 25 for items in pages)
    assert relevant.count('API External Resource') == 1
    assert 'API External Resource Hidden' not in relevant
    assert 'API Resource Hidden' not in relevant
    assert len(set(relevant)) == 26

    client.get(f'/api/resources/{hidden_resource.id.hex}', status=404)
    client.get(f'/api/resources/{hidden_external.id.hex}', status=404)


def test_api_people_endpoint_hides_unpublished_entries(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(Person(
        first_name='Public',
        last_name='Person',
    ))
    hidden_person = Person(
        first_name='Hidden',
        last_name='Person',
        publication_start=utcnow() + timedelta(days=1),
    )
    session.add(hidden_person)
    transaction.commit()

    items = api_items(client, '/api/people')
    titles = {api_item_data(item)['title'] for item in items}

    assert 'Person Public' in titles
    assert 'Person Hidden' not in titles

    client.get(f'/api/people/{hidden_person.id.hex}', status=404)


def test_api_meetings_endpoint_hides_private_entries(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    public_meeting = Meeting(
        title='Public Meeting',
        start_datetime=utcnow(),
        address='Town Hall',
    )
    hidden_meeting = Meeting(
        title='Hidden Meeting',
        start_datetime=utcnow(),
        address='Secret Hall',
    )
    hidden_meeting.access = 'private'
    session.add(public_meeting)
    session.add(hidden_meeting)
    transaction.commit()

    items = api_items(client, '/api/meetings')
    titles = {api_item_data(item)['title'] for item in items}

    assert 'Public Meeting' in titles
    assert 'Hidden Meeting' not in titles

    client.get(f'/api/meetings/{hidden_meeting.id.hex}', status=404)


def test_api_political_businesses_endpoint_hides_private_entries(
    client: Client, town_app: TestTownApp
) -> None:
    session = town_app.session()
    session.add(PoliticalBusiness(
        title='Public Business',
        number='2024.010',
        political_business_type='motion',
        status='pendent_legislative',
    ))
    hidden_business = PoliticalBusiness(
        title='Hidden Business',
        number='2024.011',
        political_business_type='motion',
        status='pendent_legislative',
    )
    hidden_business.access = 'private'
    session.add(hidden_business)
    transaction.commit()

    items = api_items(client, '/api/political_businesses')
    titles = {api_item_data(item)['title'] for item in items}

    assert 'Public Business' in titles
    assert 'Hidden Business' not in titles

    client.get(
        f'/api/political_businesses/{hidden_business.id.hex}',
        status=404,
    )
