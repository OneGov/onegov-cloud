import transaction

from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.ballot import Election
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.tests import login
from unittest.mock import patch
from webtest import TestApp as Client
from webtest import Upload


def create_vote(app):
    client = Client(app)
    login(client)
    new = client.get('/manage/votes/new-vote')
    new.form['vote_de'] = 'Vote'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'federation'
    new.form.submit()


def create_election(app, type):
    client = Client(app)
    login(client)
    new = client.get('/manage/elections/new-election')
    new.form['election_de'] = 'Election'
    new.form['date'] = date(2015, 1, 1)
    new.form['mandates'] = 1
    new.form['election_type'] = type
    new.form['domain'] = 'federation'
    new.form.submit()


def test_view_rest_authenticate(election_day_app):
    client = Client(election_day_app)

    client.post('/upload', status=401)

    client.authorization = ('Basic', ('', 'password'))
    client.post('/upload', status=401)

    collection = UploadTokenCollection(election_day_app.session())
    token = collection.create()
    transaction.commit()
    client.post('/upload', status=401)

    client.authorization = ('Basic', ('', token))
    client.post('/upload', status=400)

    collection.clear()
    transaction.commit()
    client.post('/upload', status=401)


def test_view_rest_validation(election_day_app):
    token = UploadTokenCollection(election_day_app.session()).create()
    transaction.commit()

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    # No parameters
    result = client.post('/upload', status=400).json
    assert result['status'] == 'error'
    assert result['errors'] == {
        'id': [{'message': 'This field is required.'}],
        'results': [{'message': 'This field is required.'}],
        'type': [{'message': 'This field is required.'}],
    }

    # Invalid type
    result = client.post('/upload', status=400, params=(('type', 'xyz'),)).json
    assert result['errors']['type'] == [{'message': 'Not a valid choice'}]

    # No vote
    params = (
        ('id', 'vote-id'),
        ('type', 'vote'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{'message': 'Invalid id'}]

    # No election
    params = (
        ('id', 'election-id'),
        ('type', 'election'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{'message': 'Invalid id'}]

    # Wrong election type
    create_election(election_day_app, 'majorz')
    params = (
        ('id', 'election'),
        ('type', 'parties'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{
        'message': 'Use an election based on proportional representation'
    }]


def test_view_rest_translations(election_day_app):
    token = UploadTokenCollection(election_day_app.session()).create()
    transaction.commit()

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    params = (
        ('id', 'vote-id'),
        ('type', 'vote'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )

    # Default
    result = client.post('/upload', status=400).json
    assert result['errors']['id'][0]['message'] == 'This field is required.'

    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'][0]['message'] == 'Invalid id'

    # Invalid header
    headers = [('Accept-Language', 'xxx')]
    result = client.post('/upload', status=400, headers=headers).json
    assert result['errors']['id'][0]['message'] == 'This field is required.'

    result = client.post('/upload', status=400, headers=headers, params=params)
    result = result.json
    assert result['errors']['id'][0]['message'] == 'Invalid id'

    # German
    headers = [('Accept-Language', 'de_CH')]
    result = client.post('/upload', status=400, headers=headers).json
    assert result['errors']['id'][0]['message'] == 'Dieses Feld wird benötigt.'

    result = client.post('/upload', status=400, headers=headers, params=params)
    result = result.json
    assert result['errors']['id'][0]['message'] == 'Ungültige ID'


def test_view_rest_vote(election_day_app):
    token = UploadTokenCollection(election_day_app.session()).create()
    transaction.commit()

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    create_vote(election_day_app)

    params = (
        ('id', 'vote'),
        ('type', 'vote'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )

    with patch(
        'onegov.election_day.views.upload.rest.import_vote_internal',
        return_value=[]
    ) as import_:
        result = client.post('/upload', params=params)
        assert result.json['status'] == 'success'

        assert import_.called
        assert isinstance(import_.call_args[0][0], Vote)
        assert 1701 in import_.call_args[0][1]
        assert isinstance(import_.call_args[0][2], BytesIO)
        assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_election(election_day_app):
    token = UploadTokenCollection(election_day_app.session()).create()
    transaction.commit()

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    create_election(election_day_app, 'proporz')

    params = (
        ('id', 'election'),
        ('type', 'election'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )

    with patch(
        'onegov.election_day.views.upload.rest.import_election_internal',
        return_value=[]
    ) as import_:
        result = client.post('/upload', params=params)
        assert result.json['status'] == 'success'

        assert import_.called
        assert isinstance(import_.call_args[0][0], Election)
        assert 1701 in import_.call_args[0][1]
        assert isinstance(import_.call_args[0][2], BytesIO)
        assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_parties(election_day_app):
    token = UploadTokenCollection(election_day_app.session()).create()
    transaction.commit()

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    create_election(election_day_app, 'proporz')

    params = (
        ('id', 'election'),
        ('type', 'parties'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )

    with patch(
        'onegov.election_day.views.upload.rest.import_party_results',
        return_value=[]
    ) as import_:
        result = client.post('/upload', params=params)
        assert result.json['status'] == 'success'

        assert import_.called
        assert isinstance(import_.call_args[0][0], Election)
        assert isinstance(import_.call_args[0][1], BytesIO)
        assert import_.call_args[0][2] == 'application/octet-stream'
