from __future__ import annotations

import transaction

from onegov.org.models.meeting import Meeting
from onegov.org.models.parliament import (
    RISCommission, RISParliamentarian, RISParliamentaryGroup)
from onegov.org.models.political_business import PoliticalBusiness
from sedate import utcnow
from uuid import uuid4

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


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


def test_api_lists_ris_endpoints(client: Client) -> None:
    response = client.get('/api')
    assert response.status_code == 200

    data = response.json
    queries = data['collection']['queries']
    endpoint_names = [q['rel'] for q in queries]

    assert 'meetings' not in endpoint_names
    assert 'political_businesses' not in endpoint_names
    assert 'parliamentarians' not in endpoint_names
    assert 'commissions' not in endpoint_names
    assert 'parliamentary_groups' not in endpoint_names

    client.app.org.ris_enabled = True
    transaction.commit()
    response = client.get('/api')
    assert response.status_code == 200

    data = response.json
    queries = data['collection']['queries']
    endpoint_names = [q['rel'] for q in queries]

    assert 'meetings' in endpoint_names
    assert 'political_businesses' in endpoint_names
    assert 'parliamentarians' in endpoint_names
    assert 'commissions' in endpoint_names
    assert 'parliamentary_groups' in endpoint_names


def test_api_meetings_endpoint(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
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


def test_api_political_businesses_endpoint(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
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


def test_api_parliamentarians_endpoint(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
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


def test_api_commissions_endpoint(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
    session.add(RISCommission(name='Finance Commission'))
    transaction.commit()

    response = client.get('/api/commissions')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = api_item_data(items[0])
    assert item_data['name'] == 'Finance Commission'


def test_api_parliamentary_groups_endpoint(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
    session.add(RISParliamentaryGroup(name='Green Party Group'))
    transaction.commit()

    response = client.get('/api/parliamentary_groups')
    assert response.status_code == 200
    data = response.json
    items = data['collection']['items']
    assert len(items) == 1

    item_data = {d['name']: d['value'] for d in items[0]['data']}
    assert item_data['name'] == 'Green Party Group'


def test_api_meetings_endpoint_hides_private_entries(client: Client) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
    public_meeting = Meeting(
        title='Public Meeting',
        start_datetime=utcnow(),
        address='Town Hall',
    )
    hidden_id = uuid4()
    hidden_meeting = Meeting(
        id=hidden_id,
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

    client.get(f'/api/meetings/{hidden_id.hex}', status=404)


def test_api_political_businesses_endpoint_hides_private_entries(
    client: Client
) -> None:
    session = client.app.session()
    client.app.org.ris_enabled = True
    session.add(PoliticalBusiness(
        title='Public Business',
        number='2024.010',
        political_business_type='motion',
        status='pendent_legislative',
    ))
    hidden_id = uuid4()
    hidden_business = PoliticalBusiness(
        id=hidden_id,
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
        f'/api/political_businesses/{hidden_id.hex}',
        status=404,
    )
