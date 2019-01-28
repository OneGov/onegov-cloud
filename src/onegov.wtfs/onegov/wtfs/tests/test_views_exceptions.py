from webtest import TestApp as Client


def test_view_exceptions(wtfs_app):
    client = Client(wtfs_app)

    # todo:
    # assert (
    #     "Sie versuchen eine Seite zu öffnen, für die Sie nicht autorisiert "
    #     "sind"
    # ) in client.get('/xxx', status=403)

    assert (
        "Die angeforderte Seite konnte nicht gefunden werden."
    ) in client.get('/abstimmungen', status=404)
