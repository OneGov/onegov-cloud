def test_principal_app_cache(election_day_app_zg):
    assert election_day_app_zg.principal.name == "Kanton Govikon"
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal.name == "Kanton Govikon"


def test_principal_app_not_existant(election_day_app_zg):
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal is None
