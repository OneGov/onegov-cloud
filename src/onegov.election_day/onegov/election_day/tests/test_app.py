def test_principal_app_cache(election_day_app):
    assert election_day_app.principal.name == "Kanton Govikon"
    election_day_app.filestorage.remove('principal.yml')
    assert election_day_app.principal.name == "Kanton Govikon"


def test_principal_app_not_existant(election_day_app):
    election_day_app.filestorage.remove('principal.yml')
    assert election_day_app.principal is None
