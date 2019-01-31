from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.forms import UserGroupForm


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
    groups = UserGroupCollection(session)
    group = groups.add(name="Gruppe Winterthur")
    groups.add(name="Gruppe Aesch")

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Gemeinde Winterthur",
        bfs_number=230,
        group_id=group.id
    )

    # Test choices
    form = MunicipalityForm()
    form.request = DummyRequest(session)
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == ["", "Gruppe Aesch"]

    form.model = municipalities
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == ["", "Gruppe Aesch"]

    form.model = municipality
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == [
        "", "Gruppe Aesch", "Gruppe Winterthur"
    ]

    # Test apply / update
    form = MunicipalityForm()
    form.apply_model(municipality)
    assert form.name.data == "Gemeinde Winterthur"
    assert form.bfs_number.data == 230
    assert form.group_id.data == str(group.id)

    form.name.data = "Gemeinde Adlikon"
    form.bfs_number.data = 21
    form.group_id.data = groups.add(name="Gruppe Adlikon").id
    form.update_model(municipality)
    assert municipality.name == "Gemeinde Adlikon"
    assert municipality.bfs_number == 21
    assert municipality.group.name == "Gruppe Adlikon"

    form.group_id.data = ''
    form.update_model(municipality)
    session.flush()
    session.expire_all()
    assert municipality.group_id is None
    assert municipality.group is None

    # Test validation
    form = MunicipalityForm()
    form.request = DummyRequest(session)
    form.on_request()
    assert not form.validate()

    form = MunicipalityForm(
        DummyPostData({
            'name': "Gemeinde Winterthur",
            'bfs_number': '230',
            'group_id': ''
        })
    )
    form.request = DummyRequest(session)
    form.on_request()
    assert form.validate()

    form = MunicipalityForm(
        DummyPostData({
            'name': "Gemeinde Winterthur",
            'bfs_number': '230',
            'group_id': group.id
        })
    )
    form.request = DummyRequest(session)
    form.on_request()
    assert form.validate()


def test_user_group_form(session):
    # Test apply / update
    groups = UserGroupCollection(session)
    group = groups.add(name="Gruppe Winterthur")

    form = UserGroupForm()
    form.apply_model(group)
    assert form.name.data == "Gruppe Winterthur"

    form.name.data = "Gruppe Adlikon"
    form.update_model(group)
    assert group.name == "Gruppe Adlikon"

    # Test validation
    form = UserGroupForm()
    assert not form.validate()

    form = UserGroupForm(DummyPostData({'name': "Gruppe Winterthur"}))
    assert form.validate()
