
def test_principal_app_cache(gazette_app):
    assert gazette_app.principal.name == "Govikon"
    gazette_app.filestorage.remove('principal.yml')
    assert gazette_app.principal.name == "Govikon"


def test_principal_app_not_existant(gazette_app):
    gazette_app.filestorage.remove('principal.yml')
    assert gazette_app.principal is None


def test_app_theme_options(gazette_app):
    assert gazette_app.theme_options == {'primary-color': '#006FB5'}
