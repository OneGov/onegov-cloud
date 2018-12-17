from onegov.swissvotes.models import TranslatablePage
from transaction import commit
from webtest import TestApp as Client


def test_view_home(swissvotes_app):
    client = Client(swissvotes_app)
    home = client.get('/').maybe_follow()
    assert "Startseite" in home
    assert home.request.url.endswith('page/home')

    session = swissvotes_app.session()
    session.delete(session.query(TranslatablePage).filter_by(id='home').one())
    commit()

    home = client.get('/').maybe_follow()
    assert not home.request.url.endswith('page/home')
