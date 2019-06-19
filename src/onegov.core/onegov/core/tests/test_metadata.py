import morepath

from onegov.core.framework import Framework
from webtest import TestApp as Client


def test_metadata(redis_url):

    class App(Framework):
        pass

    morepath.commit(App)

    app = App()
    app.configure_application(redis_url=redis_url)
    app.namespace = 'tests'
    app.set_application_id('tests/foo')

    client = Client(app)

    public = client.get('/metadata/public').json
    assert 'identity' in public
    assert 'fqdn' not in public
    assert 'application_id' not in public

    identity = client.get('/metadata/public/identity')
    assert public['identity'] == identity.text
    assert app.metadata.identity == identity.text
