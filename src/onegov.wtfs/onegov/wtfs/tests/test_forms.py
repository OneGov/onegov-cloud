from cgi import FieldStorage
from datetime import date
from io import BytesIO
from mock import MagicMock
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import DeleteMunicipalityDatesForm
from onegov.wtfs.forms import ImportMunicipalityDataForm
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.forms import UnrestrictedUserForm
from onegov.wtfs.forms import UserForm
from onegov.wtfs.forms import UserGroupForm
from onegov.wtfs.models import PickupDate


class App(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class Identity(object):
    def __init__(self, groupid):
        self.groupid = groupid


class Request(object):
    def __init__(self, session, principal=None, groupid=None):
        self.app = App(session, principal)
        self.session = session
        self.identity = Identity(groupid)

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate()


class PostData(dict):
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
    form.request = Request(session)
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == ["Gruppe Aesch"]

    form.model = municipalities
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == ["Gruppe Aesch"]

    form.model = municipality
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == [
        "Gruppe Aesch", "Gruppe Winterthur"
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

    # Test validation
    form = MunicipalityForm()
    form.request = Request(session)
    form.on_request()
    assert not form.validate()

    form = MunicipalityForm(
        PostData({
            'name': "Gemeinde Winterthur",
            'bfs_number': '230',
            'group_id': ''
        })
    )
    form.request = Request(session)
    form.on_request()
    assert not form.validate()

    form = MunicipalityForm(
        PostData({
            'name': "Gemeinde Winterthur",
            'bfs_number': '230',
            'group_id': group.id
        })
    )
    form.request = Request(session)
    form.on_request()
    assert form.validate()


def test_import_municipality_data_form(session):
    groups = UserGroupCollection(session)
    municipalities = MunicipalityCollection(session)
    municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=groups.add(name="Winterthur").id
    )
    municipalities.add(
        name="Adlikon",
        bfs_number=21,
        group_id=groups.add(name="Adlikon").id
    )

    # Test apply
    form = ImportMunicipalityDataForm()
    form.request = Request(session)

    form.file.data = {
        21: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]},
        241: {'dates': [date(2019, 1, 3), date(2019, 1, 9)]},
        230: {'dates': [date(2019, 1, 4), date(2019, 1, 10)]}
    }
    form.update_model(municipalities)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7)]),
        (230, [date(2019, 1, 4), date(2019, 1, 10)])
    ]

    # Test validation
    form = ImportMunicipalityDataForm()
    form.request = Request(session)
    assert not form.validate()

    field_storage = FieldStorage()
    field_storage.file = BytesIO(
        "Gemeinde-Nr,Vordefinierte Termine\n21,12.2.2015".encode('utf-8')
    )
    field_storage.type = 'text/csv'
    field_storage.filename = 'test.csv'
    form.file.process(PostData({'file': field_storage}))

    assert form.validate()


def test_delete_municipality_dates_form(session):
    groups = UserGroupCollection(session)
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=groups.add(name="Winterthur").id
    )

    # Test apply / update
    form = DeleteMunicipalityDatesForm()
    form.request = Request(session)
    form.apply_model(municipality)
    assert form.start.data is None
    assert form.end.data is None

    form.start.data = date(2019, 1, 1)
    form.end.data = date(2019, 12, 31)
    form.update_model(municipality)

    municipality.pickup_dates.append(PickupDate(date=date(2018, 12, 31)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 1)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 6, 6)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 12, 31)))
    municipality.pickup_dates.append(PickupDate(date=date(2020, 1, 1)))

    form.apply_model(municipality)
    assert form.start.data == date(2018, 12, 31)
    assert form.end.data == date(2020, 1, 1)

    form.start.data = date(2019, 1, 1)
    form.end.data = date(2019, 12, 31)
    form.update_model(municipality)
    assert [d.date for d in municipality.pickup_dates] == [
        date(2018, 12, 31), date(2020, 1, 1)
    ]

    # Test validation
    form = DeleteMunicipalityDatesForm()
    assert not form.validate()

    form = DeleteMunicipalityDatesForm(
        PostData({'start': "2019-01-01", 'end': "2019-12-31"})
    )
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

    form = UserGroupForm(PostData({'name': "Gruppe Winterthur"}))
    assert form.validate()


def test_user_form(session):
    groups = UserGroupCollection(session)
    group = groups.add(name="Gruppe Winterthur")

    # Test apply / update
    form = UserForm()
    form.request = Request(session, groupid=group.id.hex)

    user = User()
    form.realname.data = "Petra Muster"
    form.username.data = "petra.muster@winterthur.ch"
    form.contact.data = False
    form.update_model(user)
    assert user.realname == "Petra Muster"
    assert user.username == "petra.muster@winterthur.ch"
    assert user.group_id == group.id.hex
    assert user.data['contact'] is False
    assert user.password_hash
    assert user.modified

    users = UserCollection(session)
    user = users.add(
        realname="Hans Muster",
        username="hans.muster@winterthur.ch",
        role='invalid',
        password='abcd',
    )
    user.logout_all_sessions = MagicMock()
    password_hash = user.password_hash

    form.apply_model(user)
    assert form.realname.data == "Hans Muster"
    assert form.username.data == "hans.muster@winterthur.ch"
    assert form.contact.data is False

    form.realname.data = "Hans-Peter Muster"
    form.username.data = "hans-peter.muster@winterthur.ch"
    form.contact.data = True
    form.update_model(user)
    assert user.realname == "Hans-Peter Muster"
    assert user.username == "hans-peter.muster@winterthur.ch"
    assert user.group_id == group.id.hex
    assert user.data['contact'] is True
    assert user.password_hash == password_hash
    assert user.logout_all_sessions.called is True

    # Test validation
    form = UserForm()
    form.request = Request(session, groupid=group.id.hex)
    assert not form.validate()

    form = UserForm(PostData({
        'realname': "Hans-Peter Muster",
        'username': "hans-peter.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group.id.hex)
    assert not form.validate()
    assert form.errors == {'username': ['This value already exists.']}

    form = UserForm(PostData({
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group.id.hex)
    assert form.validate()


def test_unrestricted_user_form(session):
    groups = UserGroupCollection(session)
    group_1 = groups.add(name="Gruppe Winterthur")
    group_2 = groups.add(name="Gruppe Aesch")

    # Test choices
    form = UnrestrictedUserForm()
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == [
        "- none -", "Gruppe Winterthur", "Gruppe Aesch"
    ]
    assert form.role.choices == [
        ('editor', "Editor"),
        ('member', "Member")
    ]

    # Test apply / update
    user = User()
    form.role.data = "member"
    form.group_id.data = None
    form.realname.data = "Petra Muster"
    form.username.data = "petra.muster@winterthur.ch"
    form.contact.data = False
    form.update_model(user)
    assert user.role == 'member'
    assert user.realname == "Petra Muster"
    assert user.username == "petra.muster@winterthur.ch"
    assert user.group_id is None
    assert user.data['contact'] is False
    assert user.password_hash
    assert user.modified

    users = UserCollection(session)
    user = users.add(
        realname="Hans Muster",
        username="hans.muster@winterthur.ch",
        role='member',
        password='abcd',
    )
    user.group_id = group_1.id
    user.logout_all_sessions = MagicMock()
    password_hash = user.password_hash

    form.apply_model(user)
    assert form.role.data == 'member'
    assert form.group_id.data == str(group_1.id)
    assert form.realname.data == "Hans Muster"
    assert form.username.data == "hans.muster@winterthur.ch"
    assert form.contact.data is False

    form.role.data = 'admin'
    form.group_id.data = str(group_2.id)
    form.realname.data = "Hans-Peter Muster"
    form.username.data = "hans-peter.muster@winterthur.ch"
    form.contact.data = True
    form.update_model(user)
    assert user.realname == "Hans-Peter Muster"
    assert user.username == "hans-peter.muster@winterthur.ch"
    assert user.group_id == str(group_2.id)
    assert user.data['contact'] is True
    assert user.password_hash == password_hash
    assert user.logout_all_sessions.called is True

    # Test validation
    form = UnrestrictedUserForm()
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert not form.validate()

    form = UnrestrictedUserForm(PostData({
        'role': 'member',
        'realname': "Hans-Peter Muster",
        'username': "hans-peter.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert not form.validate()
    assert form.errors == {'username': ['This value already exists.']}

    form = UnrestrictedUserForm(PostData({
        'role': 'admin',
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert not form.validate()
    assert form.errors == {'role': ['Not a valid choice']}

    form = UnrestrictedUserForm(PostData({
        'role': 'member',
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert form.validate()

    form = UnrestrictedUserForm(PostData({
        'role': 'editor',
        'group_id': str(group_2.id),
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=group_1.id.hex)
    form.on_request()
    assert form.validate()
