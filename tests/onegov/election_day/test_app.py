import json
import os
import transaction


def test_principal_app_cache(election_day_app):
    assert election_day_app.principal.name == "Kanton Govikon"
    election_day_app.filestorage.remove('principal.yml')
    assert election_day_app.principal.name == "Kanton Govikon"


def test_principal_app_not_existant(election_day_app):
    election_day_app.filestorage.remove('principal.yml')
    assert election_day_app.principal is None


def test_send_sms(election_day_app, temporary_directory):
    election_day_app.send_sms('+41791112233', 'text')
    transaction.commit()

    path = os.path.join(
        election_day_app.configuration['sms_directory'],
        election_day_app.schema
    )
    sms = os.listdir(path)
    assert len(sms) == 1

    with open(os.path.join(path, sms[0])) as file:
        data = json.loads(file.read())
        assert data['receivers'] == ['+41791112233']
        assert data['content'] == 'text'


def test_send_sms_batch(election_day_app, temporary_directory):
    election_day_app.send_sms(
        [f'+4179111{digits}' for digits in range(1000, 3700)],
        'text'
    )
    transaction.commit()

    path = os.path.join(
        election_day_app.configuration['sms_directory'],
        election_day_app.schema
    )
    sms = sorted(os.listdir(path))
    assert len(sms) == 3

    with open(os.path.join(path, sms[0])) as file:
        data = json.loads(file.read())
        assert len(data['receivers']) == 1000
        assert data['content'] == 'text'

    with open(os.path.join(path, sms[1])) as file:
        data = json.loads(file.read())
        assert len(data['receivers']) == 1000
        assert data['content'] == 'text'

    with open(os.path.join(path, sms[2])) as file:
        data = json.loads(file.read())
        assert len(data['receivers']) == 700
        assert data['content'] == 'text'
