
def test_app(swissvotes_app):
    assert swissvotes_app.principal
    assert swissvotes_app.static_content_pages == {
        'home', 'disclaimer', 'imprint', 'data-protection'
    }
