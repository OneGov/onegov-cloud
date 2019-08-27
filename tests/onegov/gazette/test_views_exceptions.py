from webtest import TestApp as Client


def test_view_exceptions(gazette_app):
    client = Client(gazette_app)

    assert (
        "Sie versuchen eine Seite zu öffnen, für die Sie nicht autorisiert "
        "sind"
    ) in client.get('/groups', status=403)

    assert (
        "Die angeforderte Seite konnte nicht gefunden werden."
    ) in client.get('/groupz', status=404)
