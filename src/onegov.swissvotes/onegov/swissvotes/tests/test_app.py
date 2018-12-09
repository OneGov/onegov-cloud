from onegov.swissvotes.collections import TranslatablePageCollection


def test_app_principal(swissvotes_app):
    assert swissvotes_app.principal


def test_app_initial_content(swissvotes_app):
    pages = TranslatablePageCollection(swissvotes_app.session())

    assert {page.title for page in pages.query()} == {
        'Startseite',
        'Datensatz',
        'Über uns',
        'Kontakt',
        'Disclaimer',
        'Impressum'
    }
