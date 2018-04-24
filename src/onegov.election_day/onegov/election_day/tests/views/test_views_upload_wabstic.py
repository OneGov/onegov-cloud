from datetime import date
from onegov.election_day.tests.common import login
from webtest import TestApp as Client
from webtest import Upload
from unittest.mock import patch


def add_data_source(client, name='name', upload_type='vote', fill=False):
    login(client)

    manage = client.get('/manage/sources/new-source')
    manage.form['name'] = 'source'
    manage.form['upload_type'] = upload_type
    manage = manage.form.submit().follow()

    token = manage.pyquery(('h2 small')).text().split('/')[1].strip()
    id_ = manage.request.url.split('/source/')[1].split('/')[0]

    if fill:
        if upload_type == 'vote':
            manage = client.get('/manage/votes/new-vote')
            manage.form['vote_de'] = 'item'
            manage.form['date'] = date(2015, 1, 1)
            manage.form['domain'] = 'federation'
            manage.form.submit()
        else:
            manage = client.get('/manage/elections/new-election')
            manage.form['election_de'] = 'item'
            manage.form['date'] = date(2015, 1, 1)
            manage.form['mandates'] = 1
            manage.form['election_type'] = upload_type
            manage.form['domain'] = 'federation'
            manage.form.submit()

        manage = client.get('/manage/source/{}/items/new-item'.format(id_))
        manage.form['item'] = 'item'
        manage.form['district'] = '1'
        manage.form['number'] = '2'
        manage = manage.form.submit().follow()

    return id_, token


def regenerate_token(client, id_):
    login(client)

    client.get('/data-source/{}/generate-token'.format(id_)).form.submit()

    manage = client.get('/manage/source/{}/items'.format(id_))
    token = manage.pyquery(('h2 small')).text().split('/')[1].strip()
    return token


def test_view_wabstic_authenticate(election_day_app):
    client = Client(election_day_app)
    urls = ('vote', 'majorz', 'proporz')

    def post(url):
        return client.post('/upload-wabsti-{}'.format(url), expect_errors=True)

    assert all((post(url).status_code == 403 for url in urls))

    client.authorization = ('Basic', ('', 'password'))

    assert all((post(url).status_code == 403 for url in urls))

    id_, token = add_data_source(Client(election_day_app))

    assert all((post(url).status_code == 403 for url in urls))

    client.authorization = ('Basic', ('', token))

    assert all((post(url).status_code == 200 for url in urls))

    regenerate_token(Client(election_day_app), id_)

    assert all((post(url).status_code == 403 for url in urls))


def test_view_wabstic_translations(election_day_app):
    id_, token = add_data_source(Client(election_day_app), fill=True)

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    params = (
        ('sg_geschaefte', Upload('sg_geschaefte.txt', 'a'.encode('utf-8'))),
        ('sg_gemeinden', Upload('sg_gemeinden.txt', 'a'.encode('utf-8'))),
    )

    # Default
    result = client.post('/upload-wabsti-vote')
    assert result.json['errors']['sg_gemeinden'] == ['This field is required.']

    result = client.post('/upload-wabsti-majorz')
    assert result.json['errors']['data_source'] == [
        'The data source is not configured properly'
    ]

    result = client.post('/upload-wabsti-vote', params=params)
    assert result.json['errors']['item'][0]['message'] == (
        'Not a valid xls/xlsx file.'
    )

    # Invalid header
    headers = [('Accept-Language', 'xxx')]
    result = client.post('/upload-wabsti-vote', headers=headers)
    assert result.json['errors']['sg_gemeinden'] == ['This field is required.']

    result = client.post('/upload-wabsti-majorz', headers=headers)
    assert result.json['errors']['data_source'] == [
        'The data source is not configured properly'
    ]

    result = client.post('/upload-wabsti-vote', headers=headers, params=params)
    assert result.json['errors']['item'][0]['message'] == (
        'Not a valid xls/xlsx file.'
    )

    # German
    headers = [('Accept-Language', 'de_CH')]
    result = client.post('/upload-wabsti-vote', headers=headers)
    assert result.json['errors']['sg_gemeinden'] == [
        'Dieses Feld wird benötigt.'
    ]

    result = client.post('/upload-wabsti-majorz', headers=headers)
    assert result.json['errors']['data_source'] == [
        'Die Datenquellekonfiguration ist ungültig'
    ]

    result = client.post('/upload-wabsti-vote', headers=headers, params=params)
    assert result.json['errors']['item'][0]['message'] == (
        'Keine gültige XLS/XLSX Datei.'
    )

    # Italian
    headers = [('Accept-Language', 'it_CH')]
    result = client.post('/upload-wabsti-vote', headers=headers)
    assert result.json['errors']['sg_gemeinden'] == [
        'Questo campo è obbligatorio.'
    ]

    result = client.post('/upload-wabsti-majorz', headers=headers)
    assert result.json['errors']['data_source'] == [
        'L\'origine dati non è configurata correttamente'
    ]

    result = client.post('/upload-wabsti-vote', headers=headers, params=params)
    assert result.json['errors']['item'][0]['message'] == (
        'Nessun file XLS/XLSX valido.'
    )


def test_view_wabstic_vote(election_day_app):
    id_, token = add_data_source(Client(election_day_app), fill=True)

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    params = [
        (name, Upload('{}.csv'.format(name), 'a'.encode('utf-8')))
        for name in ('sg_geschaefte', 'sg_gemeinden')
    ]

    with patch(
        'onegov.election_day.views.upload.wabsti_exporter.import_vote_wabstic'
    ) as import_:
        result = client.post('/upload-wabsti-vote', params=params)
        assert import_.called
        assert '1' in import_.call_args[0]
        assert '2' in import_.call_args[0]
        assert result.json['status'] == 'success'


def test_view_wabstic_majorz(election_day_app):
    id_, token = add_data_source(
        Client(election_day_app),
        upload_type='majorz',
        fill=True
    )

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    params = [
        (name, Upload('{}.csv'.format(name), 'a'.encode('utf-8')))
        for name in (
            'wm_wahl',
            'wmstatic_gemeinden',
            'wm_gemeinden',
            'wm_kandidaten',
            'wm_kandidatengde'
        )
    ]

    with patch(
        'onegov.election_day.views.upload.wabsti_exporter'
        '.import_election_wabstic_majorz'
    ) as import_:
        result = client.post('/upload-wabsti-majorz', params=params)
        assert import_.called
        assert '1' in import_.call_args[0]
        assert '2' in import_.call_args[0]
        assert result.json['status'] == 'success'


def test_view_wabstic_proporz(election_day_app):
    id_, token = add_data_source(
        Client(election_day_app),
        upload_type='proporz',
        fill=True
    )

    client = Client(election_day_app)
    client.authorization = ('Basic', ('', token))

    params = [
        (name, Upload('{}.csv'.format(name), 'a'.encode('utf-8')))
        for name in (
            'wp_wahl',
            'wpstatic_gemeinden',
            'wp_gemeinden',
            'wp_listen',
            'wp_listengde',
            'wpstatic_kandidaten',
            'wp_kandidaten',
            'wp_kandidatengde',
        )
    ]

    with patch(
        'onegov.election_day.views.upload.wabsti_exporter'
        '.import_election_wabstic_proporz'
    ) as import_:
        result = client.post('/upload-wabsti-proporz', params=params)
        assert import_.called
        assert '1' in import_.call_args[0]
        assert '2' in import_.call_args[0]
        assert result.json['status'] == 'success'
