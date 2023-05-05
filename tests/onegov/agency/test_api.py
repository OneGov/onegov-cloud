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
    with freeze_time('2023-05-02T14:05:53.473045+00:00'):
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
        page = client.get('/people').click('Person', href='new')
        page.form['academic_title'] = 'Dr.'
        page.form['first_name'] = 'Nick'
        page.form['last_name'] = 'Rivera'
        page.form.submit().follow()

        page = client.get('/organizations').click('Organisation', href='new')
        page.form['title'] = 'Hospital'
        coordiantes = get_base64_encoded_json_string(
            dict(lon=1.1, lat=-2.2, zoom=3))
        page.form['coordinates'] = coordiantes
        page = page.form.submit().follow()

        page = page.click('Mitgliedschaft', href='new')
        page.form['title'] = 'Doctor'
        page.form['person_id'].select(text='Rivera Nick')
        page.form.submit().follow()

        page = client.get('/people').click('Person', href='new')
        page.form['first_name'] = 'Edna'
        page.form['last_name'] = 'Krabappel'
        page.form.submit().follow()

        page = client.get('/organizations').click('Organisation', href='new')
        page.form['title'] = 'School'
        agency = page.form.submit().follow()

        page = agency.click('Mitgliedschaft', href='new')
        page.form['title'] = 'Teacher'
        page.form['person_id'].select(text='Krabappel Edna')
        page.form.submit().follow()

        page = agency.click('Organisation', href='new')
        page.form['title'] = 'School Board'
        page.form.submit().follow()

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
            'title': 'Doctor',
        }

        school = collection(agencies['School']).items[0]
        assert data(school) == {
            'email': '',
            'location_address': '',
            'location_code_city': '',
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
        assert data(collection(links(school)['memberships']).items[0]) == {
            'title': 'Teacher'}

        board = collection(agencies['School Board']).items[0]
        assert data(board) == {
            'email': '',
            'location_address': '',
            'location_code_city': '',
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
        assert not links(board)['organigram']
        assert data(collection(links(board)['parent']).items[0])['title'] == \
               'School'
        assert not collection(links(board)['children']).items
        assert not collection(links(board)['memberships']).items

        # People
        people = {
            data(item)['title']: item.href
            for item in collection('/api/people').items
        }
        assert set(people) == {'Krabappel Edna', 'Rivera Nick'}

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
            'title': 'Teacher'
        }

        nick = collection(people['Rivera Nick']).items[0]
        assert data(nick) == {
            'academic_title': 'Dr.',
            'location_address': '',
            'location_code_city': '',
            'postal_address': '',
            'postal_code_city': '',
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
            'title': 'Doctor'
        }

        # Memberships
        memberships = {
            item.data[0].value: item.href
            for item in collection('/api/memberships').items
        }
        assert set(memberships) == {'Doctor', 'Teacher'}

        doctor = collection(memberships['Doctor']).items[0]
        assert data(doctor) == {'title': 'Doctor'}
        assert data(collection(links(doctor)['agency']).items[0])['title'] == \
               'Hospital'
        assert data(collection(links(doctor)['person']).items[0])['title'] == \
               'Rivera Nick'

        teacher = collection(memberships['Teacher']).items[0]
        assert data(teacher) == {'title': 'Teacher'}
        assert data(collection(links(teacher)['agency']).items[0])['title'] ==\
               'School'
        assert data(collection(links(teacher)['person']).items[0])['title'] ==\
               'Krabappel Edna'
