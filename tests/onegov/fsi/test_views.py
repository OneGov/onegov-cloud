def test_view_homepage(client):
    homepage = client.get('/')

    assert "Informationen" in homepage
    assert "Kursverwaltung" in homepage
