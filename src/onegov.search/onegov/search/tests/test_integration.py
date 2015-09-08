def test_elasticsearch_available(es_client):
    assert es_client.ping()
