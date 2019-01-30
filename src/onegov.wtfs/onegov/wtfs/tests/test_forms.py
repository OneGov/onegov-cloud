from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import MunicipalityForm


class DummyPrincipal(object):
    pass


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal=None, private=False, secret=False):
        self.app = DummyApp(session, principal)
        self.session = session
        self.private = private
        self.secret = secret
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'

    def is_private(self, model):
        return self.private

    def is_secret(self, model):
        return self.secret

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate()


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_municipality_form(session):
    # Test apply / update
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name='Winterthur',
        bfs_number=230,
    )

    form = MunicipalityForm()
    form.apply_model(municipality)
    assert form.name.data == 'Winterthur'
    assert form.bfs_number.data == 230

    form.name.data = 'Adlikon'
    form.bfs_number.data = 21
    form.update_model(municipality)
    assert municipality.name == 'Adlikon'
    assert municipality.bfs_number == 21

    # Test validation
    form = MunicipalityForm()
    assert not form.validate()

    form = MunicipalityForm(
        DummyPostData({'name': 'Winterthur', 'bfs_number': '230'})
    )
    assert form.validate()
