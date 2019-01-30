
def test_view_exceptions(client):
    assert (
        "Sie versuchen eine Seite zu öffnen, für die Sie nicht autorisiert "
        "sind"
    ) in client.get('/municipalities/add', status=403)

    assert (
        "Die angeforderte Seite konnte nicht gefunden werden."
    ) in client.get('/abstimmungen', status=404)
