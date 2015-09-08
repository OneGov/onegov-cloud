from onegov.core import Framework
from onegov.search import ESIntegration


def test_app_integration(es_url):

    class App(Framework, ESIntegration):
        pass

    app = App()
    app.configure_application(elasticesarch_hosts=[es_url])

    assert app.es_client.ping()
