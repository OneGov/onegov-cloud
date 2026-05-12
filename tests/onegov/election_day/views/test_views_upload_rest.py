from __future__ import annotations

import transaction

from io import BytesIO
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
from sqlalchemy.orm import Session
from tests.onegov.election_day.common import login
from unittest.mock import patch
from webtest import TestApp as Client
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


def create_vote(app: TestApp) -> None:
    client = Client(app)
    login(client)
    new = client.get('/manage/votes/new-vote')
    new.form['external_id'] = '100'
    new.form['title_de'] = 'Vote'
    new.form['date'] = '2015-01-01'
    new.form['domain'] = 'federation'
    new.form.submit()


def create_election(
    app: TestApp,
    type: str,
    create_compound: bool = False
) -> None:

    client = Client(app)
    login(client)
    new = client.get('/manage/elections/new-election')
    new.form['external_id'] = '200'
    new.form['title_de'] = 'Election'
    new.form['date'] = '2015-01-01'
    new.form['mandates'] = 1
    new.form['type'] = type
    new.form['domain'] = 'municipality'
    new.form.submit()

    if create_compound:
        new = client.get('/manage/election-compounds/new-election-compound')
        new.form['external_id'] = '300'
        new.form['title_de'] = 'Elections'
        new.form['date'] = '2015-01-01'
        new.form['municipality_elections'] = ['election']
        new.form['domain'] = 'canton'
        new.form['domain_elections'] = 'municipality'
        new.form.submit()


def test_view_rest_authenticate(election_day_app_zg: TestApp) -> None:
    client = Client(election_day_app_zg)

    client.post('/upload', status=401)

    client.authorization = ('Basic', ('', 'password'))
    client.post('/upload', status=401)

    collection = UploadTokenCollection(election_day_app_zg.session())
    token_str = str(collection.create().token)
    transaction.commit()
    client.post('/upload', status=401)

    client.authorization = ('Basic', ('', token_str))
    client.post('/upload', status=400)

    for token in collection.query():
        collection.delete(token)
    transaction.commit()
    client.post('/upload', status=401)


def test_view_rest_validation(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    # No parameters
    result = client.post('/upload', status=400).json
    assert result['status'] == 'error'
    assert result['errors'] == {
        'id': [{'message': 'This field is required.'}],
        'results': [{'message': 'This field is required.'}],
        'type': [{'message': 'This field is required.'}],
    }

    # Invalid type #1
    result = client.post('/upload', status=400, params=(('type', 'xyz'),)).json
    assert result['errors']['type'] == [{'message': 'Not a valid choice.'}]

    # Invalid type #2 (file instead of string as type)
    params = (
        ('type', Upload('delivery.xml', 'a'.encode('utf-8'))),
        ('results', Upload('delivery.xml', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', params=params, status=400).json
    assert result['status'] == 'error'
    assert 'type' in result['errors']
    assert result['errors']['type'] == [
        {'message': 'Not a valid choice.'},
        {'message': 'A file was submitted instead of a string. '
                    'Use --form "type=xml" instead of --form "type=@file"'}
    ]

    # No vote
    params = (  # type:ignore[assignment]
        ('id', 'vote-id'),
        ('type', 'vote'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{'message': 'Invalid id'}]

    # No election or compound
    params = (  # type:ignore[assignment]
        ('id', 'election-id'),
        ('type', 'election'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{'message': 'Invalid id'}]

    # Wrong election type
    create_election(election_day_app_zg, 'majorz')
    params = (  # type:ignore[assignment]
        ('id', 'election'),
        ('type', 'parties'),
        ('results', Upload('results.csv', 'a'.encode('utf-8'))),
    )
    result = client.post('/upload', status=400, params=params).json
    assert result['errors']['id'] == [{
        'message': 'Use an election based on proportional representation'
    }]


def test_view_rest_translations(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

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
    headers = {'Accept-Language': 'xxx'}
    result = client.post('/upload', status=400, headers=headers).json
    assert result['errors']['id'][0]['message'] == 'This field is required.'

    result = client.post('/upload', status=400, headers=headers, params=params)
    result = result.json
    assert result['errors']['id'][0]['message'] == 'Invalid id'

    # German
    headers = {'Accept-Language': 'de_CH'}
    result = client.post('/upload', status=400, headers=headers).json
    assert result['errors']['id'][0]['message'] == 'Dieses Feld wird benötigt.'

    result = client.post('/upload', status=400, headers=headers, params=params)
    result = result.json
    assert result['errors']['id'][0]['message'] == 'Ungültige ID'


def test_view_rest_vote(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    create_vote(election_day_app_zg)

    for id_ in ('vote', '100'):
        params = (
            ('id', id_),
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
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_majorz(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    create_election(election_day_app_zg, 'majorz')

    for id_ in ('election', '200'):
        params = (
            ('id', id_),
            ('type', 'election'),
            ('results', Upload('results.csv', 'a'.encode('utf-8'))),
        )
        with patch(
            (
                'onegov.election_day.views.upload.rest.'
                'import_election_internal_majorz'
            ),
            return_value=[]
        ) as import_:
            result = client.post('/upload', params=params)
            assert result.json['status'] == 'success'

            assert import_.called
            assert isinstance(import_.call_args[0][0], Election)
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_proporz(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    create_election(election_day_app_zg, 'proporz', True)

    # election
    for id_ in ('election', '200'):
        with patch(
            (
                'onegov.election_day.views.upload.rest.'
                'import_election_internal_proporz'
            ),
            return_value=[]
        ) as import_:
            params = (
                ('id', id_),
                ('type', 'election'),
                ('results', Upload('results.csv', 'a'.encode('utf-8'))),
            )
            result = client.post('/upload', params=params)
            assert result.json['status'] == 'success'

            assert import_.called
            assert isinstance(import_.call_args[0][0], Election)
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'

    # compound
    for id_ in ('elections', '300'):
        with patch(
            (
                'onegov.election_day.views.upload.rest.'
                'import_election_compound_internal'
            ),
            return_value=[]
        ) as import_:
            params = (
                ('id', id_),
                ('type', 'election'),
                ('results', Upload('results.csv', 'a'.encode('utf-8'))),
            )
            result = client.post('/upload', params=params)
            assert result.json['status'] == 'success'

            assert import_.called
            assert isinstance(import_.call_args[0][0], ElectionCompound)
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_parties(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    create_election(election_day_app_zg, 'proporz', True)

    # election
    for id_ in ('election', '200'):
        with patch(
            'onegov.election_day.views.upload.rest.'
            'import_party_results_internal',
            return_value=[]
        ) as import_:
            params = (
                ('id', id_),
                ('type', 'parties'),
                ('results', Upload('results.csv', 'a'.encode('utf-8'))),
            )
            result = client.post('/upload', params=params)
            assert result.json['status'] == 'success'

            assert import_.called
            assert isinstance(import_.call_args[0][0], Election)
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'

    # compound
    for id_ in ('elections', '300'):
        with patch(
            'onegov.election_day.views.upload.rest.'
            'import_party_results_internal',
            return_value=[]
        ) as import_:
            params = (
                ('id', id_),
                ('type', 'parties'),
                ('results', Upload('results.csv', 'a'.encode('utf-8'))),
            )
            result = client.post('/upload', params=params)
            assert result.json['status'] == 'success'

            assert import_.called
            assert isinstance(import_.call_args[0][0], ElectionCompound)
            assert isinstance(import_.call_args[0][1], Canton)
            assert isinstance(import_.call_args[0][2], BytesIO)
            assert import_.call_args[0][3] == 'application/octet-stream'


def test_view_rest_xml(election_day_app_zg: TestApp) -> None:
    token = UploadTokenCollection(election_day_app_zg.session()).create()
    token_str = str(token.token)
    transaction.commit()

    client = Client(election_day_app_zg)
    client.authorization = ('Basic', ('', token_str))

    params = (
        ('type', 'xml'),
        ('results', Upload('delivery.xml', 'a'.encode('utf-8'))),
    )
    with patch(
        'onegov.election_day.views.upload.rest.import_ech',
        return_value=([], set(), set())
    ) as import_:
        result = client.post('/upload', params=params)
        assert result.json['status'] == 'success'

        assert import_.called
        assert isinstance(import_.call_args[0][0], Canton)
        assert isinstance(import_.call_args[0][1], BytesIO)
        assert isinstance(import_.call_args[0][2], Session)
