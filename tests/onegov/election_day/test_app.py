import os
import transaction


def test_principal_app_cache(election_day_app_zg):
    assert election_day_app_zg.principal.name == "Kanton Govikon"
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal.name == "Kanton Govikon"


def test_principal_app_not_existant(election_day_app_zg):
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal is None


def test_send_sms(election_day_app_zg, temporary_directory):
    election_day_app_zg.send_sms('+41791112233', 'text')
    transaction.commit()

    path = os.path.join(
        election_day_app_zg.configuration['sms_directory'],
        election_day_app_zg.schema
    )
    sms = os.listdir(path)
    assert len(sms) == 1

    with open(os.path.join(path, sms[0])) as file:
        assert file.read() == 'text'
