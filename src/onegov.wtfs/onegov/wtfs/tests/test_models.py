from onegov.wtfs.models.principal import Principal


def test_principal(session):
    principal = Principal()
    assert principal
