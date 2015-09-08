from onegov.core import Framework
from onegov.search import ESIntegration


def test_app_integration(es_url):

    class App(Framework, ESIntegration):
        pass

    app = App()
    app.configure_application(elasticsearch_hosts=[es_url])

    assert app.es_client.ping()

    # make sure we got the testing host
    assert len(app.es_client.transport.hosts) == 1
    assert app.es_client.transport.hosts[0]['port'] \
        == int(es_url.split(':')[-1])
