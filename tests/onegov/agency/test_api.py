import json
from base64 import b64encode

from collection_json import Collection
from freezegun import freeze_time


def get_base64_encoded_json_string(data):
    data = json.dumps(data)
    data = b64encode(data.encode('ascii'))
    data = data.decode('ascii')
    return data


def test_view_api(client):
    client.login_admin()  # prevent rate limit

    def collection(url):
        return Collection.from_json(client.get(url).body)

    def data(item):
        return {x.name: x.value for x in item.data}

    def links(item):
        return {x.rel: x.href for x in item.links}

    # Endpoints with query hints
    endpoints = collection('/api')
    assert endpoints.queries[0].rel == 'agencies'
    assert endpoints.queries[0].href == 'http://localhost/api/agencies'
    assert data(endpoints.queries[0]) == {'parent': None}
    assert endpoints.queries[1].rel == 'people'
    assert endpoints.queries[1].href == 'http://localhost/api/people'
    assert data(endpoints.queries[1]) == {}
    assert endpoints.queries[2].rel == 'memberships'
    assert endpoints.queries[2].href == 'http://localhost/api/memberships'
    assert data(endpoints.queries[2]) == {'agency': None, 'person': None}

    # No data yet
    assert not collection('/api/agencies').items
    assert not collection('/api/people').items
    assert not collection('/api/memberships').items

    # Add data
    with freeze_time('2023-05-08T01:00:00'):
        page = client.get('/people').click('Person', href='new')
        page.form['academic_title'] = 'Dr.'
        page.form['first_name'] = 'Nick'
        page.form['last_name'] = 'Rivera'
        page.form.submit().follow()

    with freeze_time('2023-05-08T01:01:00'):
        page = client.get('/organizations').click('Organisation', href='new')
        page.form['title'] = 'Hospital'
        coordinates = get_base64_encoded_json_string(
            dict(lon=1.1, lat=-2.2, zoom=3))
        page.form['coordinates'] = coordinates
        page = page.form.submit().follow()

    with freeze_time('2023-05-08T01:02:00'):
        page = page.click('Mitgliedschaft', href='new')
        page.form['title'] = 'Doctor'
        page.form['person_id'].select(text='Rivera Nick')
        page.form.submit().follow()

    with freeze_time('2023-05-08T01:05:00'):
        page = client.get('/people').click('Person', href='new')
        page.form['first_name'] = 'Edna'
        page.form['last_name'] = 'Krabappel'
        page.form.submit().follow()

    with freeze_time('2023-05-08T01:06:00'):
        page = client.get('/organizations').click('Organisation', href='new')
        page.form['title'] = 'School'
        agency = page.form.submit().follow()

    with freeze_time('2023-05-08T01:07:00'):
        page = agency.click('Mitgliedschaft', href='new')
        page.form['title'] = 'Teacher'
        page.form['person_id'].select(text='Krabappel Edna')
        page.form.submit().follow()

    with freeze_time('2023-05-08T01:10:00'):
        page = agency.click('Organisation', href='new')
        page.form['title'] = 'School Board'
        page.form.submit().follow()

    assert collection('/api/agencies').items
    assert collection('/api/people').items
    assert collection('/api/memberships').items

    # Agencies
    agencies = {
        item.data[0].value: item.href
        for item in collection('/api/agencies').items
    }
    assert set(agencies) == {'Hospital', 'School', 'School Board'}

    hospital = collection(agencies['Hospital']).items[0]
    assert data(hospital) == {
        'email': '',
        'location_address': '',
        'location_code_city': '',
        'modified': '2023-05-08T01:01:00+00:00',
        'opening_hours': '',
        'phone': '',
        'phone_direct': '',
        'portrait': '',
        'postal_address': '',
        'postal_code_city': '',
        'title': 'Hospital',
        'website': '',
        'geo_location': dict(lon=1.1, lat=-2.2, zoom=3),
    }
    assert not links(hospital)['organigram']
    assert not links(hospital)['parent']
    assert not collection(links(hospital)['children']).items
    assert data(collection(links(hospital)['memberships']).items[0]) == {
        'modified': '2023-05-08T01:02:00+00:00',
        'title': 'Doctor',
    }

    school = collection(agencies['School']).items[0]
    assert data(school) == {
        'email': '',
        'location_address': '',
        'location_code_city': '',
        'modified': '2023-05-08T01:06:00+00:00',
        'opening_hours': '',
        'phone': '',
        'phone_direct': '',
        'portrait': '',
        'postal_address': '',
        'postal_code_city': '',
        'title': 'School',
        'website': '',
        'geo_location': dict(lon=None, lat=None, zoom=None),
    }
    assert not links(school)['organigram']
    assert not links(school)['parent']
    assert data(collection(links(school)['children'])
                .items[0])['title'] == 'School Board'
    assert data(collection(links(school)['memberships'])
                .items[0]) == {
                    'modified': '2023-05-08T01:07:00+00:00',
                    'title': 'Teacher'
    }

    board = collection(agencies['School Board']).items[0]
    assert data(board) == {
        'email': '',
        'location_address': '',
        'location_code_city': '',
        'modified': '2023-05-08T01:10:00+00:00',
        'opening_hours': '',
        'phone': '',
        'phone_direct': '',
        'portrait': '',
        'postal_address': '',
        'postal_code_city': '',
        'title': 'School Board',
        'website': '',
        'geo_location': dict(lon=None, lat=None, zoom=None),
    }
    assert not links(school)['organigram']
    assert not links(school)['parent']
    assert data(collection(links(school)['children'])
                .items[0])['title'] == 'School Board'
    assert data(collection(links(school)['memberships']).items[0]) == {
        'title': 'Teacher',
        'modified': '2023-05-08T01:07:00+00:00',
    }

    # People
    people = {
        data(item)['title']: item.href
        for item in collection('/api/people').items
    }
    assert set(people) == {'Krabappel Edna', 'Rivera Nick'}

    nick = collection(people['Rivera Nick']).items[0]
    assert data(nick) == {
        'academic_title': 'Dr.',
        'location_address': '',
        'location_code_city': '',
        'postal_address': '',
        'postal_code_city': '',
        'modified': '2023-05-08T01:00:00+00:00',
        'born': '',
        'email': '',
        'first_name': 'Nick',
        'function': '',
        'last_name': 'Rivera',
        'notes': '',
        'parliamentary_group': '',
        'phone_direct': '',
        'phone': '',
        'political_party': '',
        'profession': '',
        'salutation': '',
        'title': 'Rivera Nick',
        'website': '',
    }
    assert not links(nick)['picture_url']
    assert not links(nick)['website']
    assert data(collection(links(nick)['memberships']).items[0]) == {
        'title': 'Doctor',
        'modified': '2023-05-08T01:02:00+00:00',
    }

    edna = collection(people['Krabappel Edna']).items[0]
    assert data(edna) == {
        'academic_title': '',
        'born': '',
        'email': '',
        'first_name': 'Edna',
        'function': '',
        'last_name': 'Krabappel',
        'location_address': '',
        'location_code_city': '',
        'modified': '2023-05-08T01:05:00+00:00',
        'notes': '',
        'parliamentary_group': '',
        'phone': '',
        'phone_direct': '',
        'political_party': '',
        'postal_address': '',
        'postal_code_city': '',
        'profession': '',
        'salutation': '',
        'title': 'Krabappel Edna',
        'website': '',
    }
    assert not links(edna)['picture_url']
    assert not links(edna)['website']
    assert data(collection(links(edna)['memberships']).items[0]) == {
        'title': 'Teacher',
        'modified': '2023-05-08T01:07:00+00:00',
    }

    # test 'first_name' url filter
    people = {
        data(item)['title']: item.href
        for item in collection('/api/people?first_name=Max').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection('/api/people?first_name=nick').items
    }
    assert set(people) == {'Rivera Nick'}

    people = {
        data(item)['title']: item.href
        for item in collection('/api/people?first_name=Edna').items
    }
    assert set(people) == {'Krabappel Edna'}

    # test 'last_name' url filter
    people = {
        data(item)['title']: item.href
        for item in collection('/api/people?last_name=Hugentobler').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection('/api/people?last_name=Krabappel').items
    }
    assert set(people) == {'Krabappel Edna'}

    # test first and lastname filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?first_name=nick&last_name=Krabappel').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?first_name=edna&last_name=Krabappel').items
    }
    assert set(people) == {'Krabappel Edna'}

    # test updated greater than filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.gt=2023-05-08T00:59:00').items
    }
    assert set(people) == {'Rivera Nick', 'Krabappel Edna'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.gt=2023-05-08T01:01:00').items
    }
    assert set(people) == {'Krabappel Edna'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.gt=2023-05-08T01:06:00').items
    }
    assert set(people) == set()

    # test updated greater equal filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.ge=2023-05-08T00:01:00').items
    }
    assert set(people) == {'Rivera Nick', 'Krabappel Edna'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.ge=2023-05-08T01:05:00').items
    }
    assert set(people) == {'Krabappel Edna'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.ge=2023-05-08T01:06:00').items
    }
    assert set(people) == set()

    # test updated equal filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.eq=2023-05-08T00:59:00').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.eq=2023-05-08T01:00:00').items
    }
    assert set(people) == {'Rivera Nick'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.eq=2023-05-08T01:05:00').items
    }
    assert set(people) == {'Krabappel Edna'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.eq=2023-05-08T01:06:00').items
    }
    assert set(people) == set()

    # test updated lower equal filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.le=2023-05-08T00:59:00').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.le=2023-05-08T01:00:00').items
    }
    assert set(people) == {'Rivera Nick'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.le=2023-05-08T01:05:00').items
    }
    assert set(people) == {'Rivera Nick', 'Krabappel Edna'}

    # test updated lower than filter
    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.lt=2023-05-08T01:00:00').items
    }
    assert set(people) == set()

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.lt=2023-05-08T01:01:00').items
    }
    assert set(people) == {'Rivera Nick'}

    people = {
        data(item)['title']: item.href
        for item in collection(
            '/api/people?updated.lt=2023-05-08T01:06:00').items
    }
    assert set(people) == {'Rivera Nick', 'Krabappel Edna'}

    # Memberships
    memberships = {
        item.data[0].value: item.href
        for item in collection('/api/memberships').items
    }
    assert set(memberships) == {'Doctor', 'Teacher'}

    doctor = collection(memberships['Doctor']).items[0]
    assert data(doctor) == {
        'title': 'Doctor',
        'modified': '2023-05-08T01:02:00+00:00',
    }
    assert data(collection(links(doctor)['agency']).items[0])['title'] == \
           'Hospital'
    assert data(collection(links(doctor)['person']).items[0])['title'] == \
           'Rivera Nick'

    teacher = collection(memberships['Teacher']).items[0]
    assert data(teacher) == {
        'title': 'Teacher',
        'modified': '2023-05-08T01:07:00+00:00',
    }
    assert data(collection(links(teacher)['agency']).
                items[0])['title'] == 'School'
    assert data(collection(links(teacher)['person']).
                items[0])['title'] == 'Krabappel Edna'
