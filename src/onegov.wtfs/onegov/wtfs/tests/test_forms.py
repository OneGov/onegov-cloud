from cgi import FieldStorage
from datetime import date
from freezegun import freeze_time
from io import BytesIO
from mock import MagicMock
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.forms import AddScanJobForm
from onegov.wtfs.forms import DailyListSelectionForm
from onegov.wtfs.forms import DeleteMunicipalityDatesForm
from onegov.wtfs.forms import EditScanJobForm
from onegov.wtfs.forms import ImportMunicipalityDataForm
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.forms import MunicipalityIdSelectionForm
from onegov.wtfs.forms import ReportSelectionForm
from onegov.wtfs.forms import UnrestrictedAddScanJobForm
from onegov.wtfs.forms import UnrestrictedEditScanJobForm
from onegov.wtfs.forms import UnrestrictedUserForm
from onegov.wtfs.forms import UserForm
from onegov.wtfs.forms import UserGroupForm
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import ScanJob


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
    def __init__(self, session, principal=None, groupid=None, roles=[]):
        self.app = App(session, principal)
        self.session = session
        self.identity = Identity(groupid)
        self.roles = roles

    def include(self, resource):
        pass

    def has_role(self, role):
        return role in self.roles

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
    assert not (form.group_id.render_kw or {}).get('disabled', False)

    # ... collection
    form.model = municipalities
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == ["Gruppe Aesch"]
    assert not (form.group_id.render_kw or {}).get('disabled', False)

    # ... municipality with no data
    form.model = municipality
    form.on_request()
    assert [c[1] for c in form.group_id.choices] == [
        "Gruppe Aesch", "Gruppe Winterthur"
    ]
    assert not (form.group_id.render_kw or {}).get('disabled', False)

    # ... municipality with data
    scan_job = ScanJob(
        group_id=group.id,
        type='normal',
        dispatch_date=date(2019, 1, 1)
    )
    municipality.scan_jobs.append(scan_job)
    session.flush()
    form.on_request()
    assert (form.group_id.render_kw or {}).get('disabled', False)

    # Test apply / update
    form = MunicipalityForm()
    form.apply_model(municipality)
    assert form.name.data == "Gemeinde Winterthur"
    assert form.bfs_number.data == 230
    assert form.group_id.data == str(group.id)

    # ... municipality with data
    form.name.data = "Gemeinde Adlikon"
    form.bfs_number.data = 21
    form.group_id.data = groups.add(name="Gruppe Adlikon").id
    form.update_model(municipality)
    assert municipality.name == "Gemeinde Adlikon"
    assert municipality.bfs_number == 21
    assert municipality.group.name == "Gruppe Winterthur"

    # ... municipality with no data
    session.delete(scan_job)
    session.flush()
    form.update_model(municipality)
    session.flush()
    session.expire_all()
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


def test_municipality_selection_form(session):
    groups = UserGroupCollection(session)
    group = groups.add(name="Gruppe Winterthur")
    groups.add(name="Gruppe Aesch")

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Gemeinde Aesch",
        bfs_number=230,
        group_id=group.id
    )

    # Test choices
    form = MunicipalityIdSelectionForm()
    form.request = Request(session)
    form.on_request()
    assert [c[1] for c in form.municipality_id.choices] == ["Gemeinde Aesch"]

    form.municipality_id.data = municipality.id
    assert form.municipality == municipality


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


def test_add_scan_job_form(session):
    groups = UserGroupCollection(session)
    group = groups.add(name="Winterthur")

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=group.id
    )
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    # Test on request
    form = AddScanJobForm()
    form.request = Request(session, groupid=group.id.hex)
    assert form.group_id == group.id.hex
    assert form.municipality_id == municipality.id
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [('normal', 'Regular shipment')]
        assert form.dispatch_date_normal.choices == [
            (date(2019, 1, 7), '07.01.2019'),
            (date(2019, 1, 8), '08.01.2019')
        ]
    form.request = Request(session, groupid=group.id.hex, roles=['editor'])
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [
            ('normal', 'Regular shipment'),
            ('express', 'Express shipment')
        ]
        assert form.dispatch_date_normal.choices == [
            (date(2019, 1, 7), '07.01.2019'),
            (date(2019, 1, 8), '08.01.2019')
        ]

    # Test update
    form.type.data = 'normal'
    form.dispatch_date_normal.data = date(2019, 1, 8)
    form.dispatch_date_express.data = date(2019, 1, 6)
    form.dispatch_boxes.data = 1
    form.dispatch_tax_forms_current_year.data = 2
    form.dispatch_tax_forms_last_year.data = 3
    form.dispatch_tax_forms_older.data = 4
    form.dispatch_single_documents.data = 5
    form.dispatch_note.data = 'Note on dispatch'
    form.dispatch_cantonal_tax_office.data = 6
    form.dispatch_cantonal_scan_center.data = 7

    model = ScanJob()
    form.update_model(model)
    assert model.municipality_id == municipality.id
    assert model.group_id == group.id.hex
    assert model.type == 'normal'
    assert model.dispatch_date == date(2019, 1, 8)
    assert model.dispatch_boxes == 1
    assert model.dispatch_tax_forms_current_year == 2
    assert model.dispatch_tax_forms_last_year == 3
    assert model.dispatch_tax_forms_older == 4
    assert model.dispatch_single_documents == 5
    assert model.dispatch_note == 'Note on dispatch'
    assert model.dispatch_cantonal_tax_office == 6
    assert model.dispatch_cantonal_scan_center == 7

    form.type.data = 'express'
    form.update_model(model)
    assert model.dispatch_date == date(2019, 1, 6)

    # Test validation
    with freeze_time("2019-01-05"):
        form = AddScanJobForm()
        form.request = Request(session, groupid=group.id.hex)
        form.on_request()
        assert not form.validate()

        form = AddScanJobForm(PostData({
            'municipality_id': municipality.id.hex,
            'type': 'normal',
            'dispatch_date_normal': '2019-01-08'
        }))
        form.request = Request(session, groupid=group.id.hex)
        form.on_request()
        assert form.validate()


def test_edit_scan_job_form(session):
    groups = UserGroupCollection(session)
    group = groups.add(name="Winterthur")

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=group.id
    )
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    # Test apply / update
    model = ScanJob()
    model.municipality_id = municipality.id
    model.group_id = group.id
    model.type = 'normal'
    model.dispatch_date = date(2019, 1, 8)
    model.dispatch_boxes = 1
    model.dispatch_tax_forms_current_year = 2
    model.dispatch_tax_forms_last_year = 3
    model.dispatch_tax_forms_older = 4
    model.dispatch_single_documents = 5
    model.dispatch_note = 'Note on dispatch'
    model.dispatch_cantonal_tax_office = 6
    model.dispatch_cantonal_scan_center = 7
    model.return_date = date(2019, 1, 10)
    model.return_boxes = 8
    model.return_scanned_tax_forms_current_year = 9
    model.return_scanned_tax_forms_last_year = 10
    model.return_scanned_tax_forms_older = 11
    model.return_scanned_single_documents = 12
    model.return_unscanned_tax_forms_current_year = 13
    model.return_unscanned_tax_forms_last_year = 14
    model.return_unscanned_tax_forms_older = 15
    model.return_unscanned_single_documents = 16
    model.return_note = 'Note on return'

    form = EditScanJobForm()
    form.request = Request(session, groupid=group.id.hex)
    form.apply_model(model)
    assert form.dispatch_boxes.data == 1
    assert form.dispatch_tax_forms_current_year.data == 2
    assert form.dispatch_tax_forms_last_year.data == 3
    assert form.dispatch_tax_forms_older.data == 4
    assert form.dispatch_single_documents.data == 5
    assert form.dispatch_note.data == 'Note on dispatch'
    assert form.dispatch_cantonal_tax_office.data == 6
    assert form.dispatch_cantonal_scan_center.data == 7
    assert form.return_date.data == date(2019, 1, 10)
    assert form.return_boxes.data == 8
    assert form.return_scanned_tax_forms_current_year.data == 9
    assert form.return_scanned_tax_forms_last_year.data == 10
    assert form.return_scanned_tax_forms_older.data == 11
    assert form.return_scanned_single_documents.data == 12
    assert form.return_unscanned_tax_forms_current_year.data == 13
    assert form.return_unscanned_tax_forms_last_year.data == 14
    assert form.return_unscanned_tax_forms_older.data == 15
    assert form.return_unscanned_single_documents.data == 16
    assert form.return_note.data == 'Note on return'

    form.dispatch_boxes.data = 10
    form.dispatch_tax_forms_current_year.data = 20
    form.dispatch_tax_forms_last_year.data = 30
    form.dispatch_tax_forms_older.data = 40
    form.dispatch_single_documents.data = 50
    form.dispatch_note.data = 'A note on the dispatch'
    form.dispatch_cantonal_tax_office.data = 60
    form.dispatch_cantonal_scan_center.data = 70
    form.return_date.data = date(2019, 1, 10)
    form.return_boxes.data = 80
    form.return_scanned_tax_forms_current_year.data = 90
    form.return_scanned_tax_forms_last_year.data = 100
    form.return_scanned_tax_forms_older.data = 110
    form.return_scanned_single_documents.data = 120
    form.return_unscanned_tax_forms_current_year.data = 130
    form.return_unscanned_tax_forms_last_year.data = 140
    form.return_unscanned_tax_forms_older.data = 150
    form.return_unscanned_single_documents.data = 160
    form.return_note.data = 'A note on the return'

    form.update_model(model)
    assert model.municipality_id == municipality.id
    assert model.group_id == group.id
    assert model.type == 'normal'
    assert model.dispatch_date == date(2019, 1, 8)
    assert model.dispatch_boxes == 10
    assert model.dispatch_tax_forms_current_year == 20
    assert model.dispatch_tax_forms_last_year == 30
    assert model.dispatch_tax_forms_older == 40
    assert model.dispatch_single_documents == 50
    assert model.dispatch_note == 'A note on the dispatch'
    assert model.dispatch_cantonal_tax_office == 60
    assert model.dispatch_cantonal_scan_center == 70
    assert model.return_date == date(2019, 1, 10)
    assert model.return_boxes == 80
    assert model.return_scanned_tax_forms_current_year == 90
    assert model.return_scanned_tax_forms_last_year == 100
    assert model.return_scanned_tax_forms_older == 110
    assert model.return_scanned_single_documents == 120
    assert model.return_unscanned_tax_forms_current_year == 130
    assert model.return_unscanned_tax_forms_last_year == 140
    assert model.return_unscanned_tax_forms_older == 150
    assert model.return_unscanned_single_documents == 160
    assert model.return_note == 'A note on the return'

    # Test validation
    form = EditScanJobForm()
    form.request = Request(session, groupid=group.id.hex)
    assert form.validate()


def test_unrestricted_add_scan_job_form(session):
    groups = UserGroupCollection(session)
    municipalities = MunicipalityCollection(session)

    group_1 = groups.add(name="Winterthur")
    municipality_1 = municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=group_1.id
    )
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    group_2 = groups.add(name="Adlikon")
    municipality_2 = municipalities.add(
        name="Adlikon",
        bfs_number=21,
        group_id=group_2.id
    )
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 17)))
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 18)))

    # Test on request
    form = UnrestrictedAddScanJobForm()
    form.request = Request(session, groupid=group_1.id.hex)
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [
            ('normal', 'Regular shipment'),
            ('express', 'Express shipment')
        ]
        assert form.municipality_id.choices == [
            (municipality_2.id.hex, 'Adlikon'),
            (municipality_1.id.hex, 'Winterthur')
        ]

    # Test update
    form.type.data = 'normal'
    form.municipality_id.data = form.municipality_id.choices[0][0]
    form.dispatch_date.data = date(2019, 1, 8)
    form.dispatch_boxes.data = 1
    form.dispatch_tax_forms_current_year.data = 2
    form.dispatch_tax_forms_last_year.data = 3
    form.dispatch_tax_forms_older.data = 4
    form.dispatch_single_documents.data = 5
    form.dispatch_note.data = 'Note on dispatch'
    form.dispatch_cantonal_tax_office.data = 6
    form.dispatch_cantonal_scan_center.data = 7

    model = ScanJob()
    form.update_model(model)
    assert model.municipality_id == municipality_2.id.hex
    assert model.group_id == group_2.id
    assert model.type == 'normal'
    assert model.dispatch_date == date(2019, 1, 8)
    assert model.dispatch_boxes == 1
    assert model.dispatch_tax_forms_current_year == 2
    assert model.dispatch_tax_forms_last_year == 3
    assert model.dispatch_tax_forms_older == 4
    assert model.dispatch_single_documents == 5
    assert model.dispatch_note == 'Note on dispatch'
    assert model.dispatch_cantonal_tax_office == 6
    assert model.dispatch_cantonal_scan_center == 7

    form.type.data = 'express'
    form.dispatch_date.data = date(2019, 1, 6)
    form.update_model(model)
    assert model.type == 'express'
    assert model.dispatch_date == date(2019, 1, 6)

    # Test validation
    with freeze_time("2019-01-05"):
        form = UnrestrictedAddScanJobForm()
        form.request = Request(session, groupid=group_1.id.hex)
        form.on_request()
        assert not form.validate()

        form = UnrestrictedAddScanJobForm(PostData({
            'municipality_id': municipality_1.id.hex,
            'type': 'normal',
            'dispatch_date': '2019-01-08'
        }))
        form.request = Request(session, groupid=group_1.id.hex)
        form.on_request()
        assert form.validate()


def test_unrestricted_edit_scan_job_form(session):
    groups = UserGroupCollection(session)
    municipalities = MunicipalityCollection(session)

    group_1 = groups.add(name="Winterthur")
    municipality_1 = municipalities.add(
        name="Winterthur",
        bfs_number=230,
        group_id=group_1.id
    )
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    group_2 = groups.add(name="Adlikon")
    municipality_2 = municipalities.add(
        name="Adlikon",
        bfs_number=21,
        group_id=group_2.id
    )
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 17)))
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 18)))

    # Test on request
    form = UnrestrictedEditScanJobForm()
    form.request = Request(session, groupid=group_1.id.hex)
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [
            ('normal', 'Regular shipment'),
            ('express', 'Express shipment')
        ]
        assert form.municipality_id.choices == [
            (municipality_2.id.hex, 'Adlikon'),
            (municipality_1.id.hex, 'Winterthur')
        ]

    # Test apply / update
    model = ScanJob()
    model.municipality_id = municipality_1.id
    model.group_id = group_1.id
    model.type = 'normal'
    model.dispatch_date = date(2019, 1, 8)
    model.dispatch_boxes = 1
    model.dispatch_tax_forms_current_year = 2
    model.dispatch_tax_forms_last_year = 3
    model.dispatch_tax_forms_older = 4
    model.dispatch_single_documents = 5
    model.dispatch_note = 'Note on dispatch'
    model.dispatch_cantonal_tax_office = 6
    model.dispatch_cantonal_scan_center = 7
    model.return_date = date(2019, 1, 10)
    model.return_boxes = 8
    model.return_scanned_tax_forms_current_year = 9
    model.return_scanned_tax_forms_last_year = 10
    model.return_scanned_tax_forms_older = 11
    model.return_scanned_single_documents = 12
    model.return_unscanned_tax_forms_current_year = 13
    model.return_unscanned_tax_forms_last_year = 14
    model.return_unscanned_tax_forms_older = 15
    model.return_unscanned_single_documents = 16
    model.return_note = 'Note on return'

    form.apply_model(model)
    assert form.type.data == 'normal'
    assert form.municipality_id.data == municipality_1.id.hex
    assert form.dispatch_date.data == date(2019, 1, 8)
    assert form.dispatch_boxes.data == 1
    assert form.dispatch_tax_forms_current_year.data == 2
    assert form.dispatch_tax_forms_last_year.data == 3
    assert form.dispatch_tax_forms_older.data == 4
    assert form.dispatch_single_documents.data == 5
    assert form.dispatch_note.data == 'Note on dispatch'
    assert form.dispatch_cantonal_tax_office.data == 6
    assert form.dispatch_cantonal_scan_center.data == 7
    assert form.return_date.data == date(2019, 1, 10)
    assert form.return_boxes.data == 8
    assert form.return_scanned_tax_forms_current_year.data == 9
    assert form.return_scanned_tax_forms_last_year.data == 10
    assert form.return_scanned_tax_forms_older.data == 11
    assert form.return_scanned_single_documents.data == 12
    assert form.return_unscanned_tax_forms_current_year.data == 13
    assert form.return_unscanned_tax_forms_last_year.data == 14
    assert form.return_unscanned_tax_forms_older.data == 15
    assert form.return_unscanned_single_documents.data == 16
    assert form.return_note.data == 'Note on return'

    form.type.data = 'express'
    form.municipality_id.data = municipality_2.id.hex
    form.dispatch_date.data = date(2019, 1, 6)
    form.dispatch_boxes.data = 10
    form.dispatch_tax_forms_current_year.data = 20
    form.dispatch_tax_forms_last_year.data = 30
    form.dispatch_tax_forms_older.data = 40
    form.dispatch_single_documents.data = 50
    form.dispatch_note.data = 'A note on the dispatch'
    form.dispatch_cantonal_tax_office.data = 60
    form.dispatch_cantonal_scan_center.data = 70
    form.return_date.data = date(2019, 1, 10)
    form.return_boxes.data = 80
    form.return_scanned_tax_forms_current_year.data = 90
    form.return_scanned_tax_forms_last_year.data = 100
    form.return_scanned_tax_forms_older.data = 110
    form.return_scanned_single_documents.data = 120
    form.return_unscanned_tax_forms_current_year.data = 130
    form.return_unscanned_tax_forms_last_year.data = 140
    form.return_unscanned_tax_forms_older.data = 150
    form.return_unscanned_single_documents.data = 160
    form.return_note.data = 'A note on the return'

    form.update_model(model)
    assert model.municipality_id == municipality_2.id.hex
    assert model.group_id == group_2.id
    assert model.type == 'express'
    assert model.dispatch_date == date(2019, 1, 6)
    assert model.dispatch_boxes == 10
    assert model.dispatch_tax_forms_current_year == 20
    assert model.dispatch_tax_forms_last_year == 30
    assert model.dispatch_tax_forms_older == 40
    assert model.dispatch_single_documents == 50
    assert model.dispatch_note == 'A note on the dispatch'
    assert model.dispatch_cantonal_tax_office == 60
    assert model.dispatch_cantonal_scan_center == 70
    assert model.return_date == date(2019, 1, 10)
    assert model.return_boxes == 80
    assert model.return_scanned_tax_forms_current_year == 90
    assert model.return_scanned_tax_forms_last_year == 100
    assert model.return_scanned_tax_forms_older == 110
    assert model.return_scanned_single_documents == 120
    assert model.return_unscanned_tax_forms_current_year == 130
    assert model.return_unscanned_tax_forms_last_year == 140
    assert model.return_unscanned_tax_forms_older == 150
    assert model.return_unscanned_single_documents == 160
    assert model.return_note == 'A note on the return'

    # Test validation
    with freeze_time("2019-01-05"):
        form = UnrestrictedEditScanJobForm()
        form.request = Request(session, groupid=group_1.id.hex)
        form.on_request()
        assert not form.validate()

        form = UnrestrictedEditScanJobForm(PostData({
            'municipality_id': municipality_1.id.hex,
            'type': 'normal',
            'dispatch_date': '2019-01-18'
        }))
        form.request = Request(session, groupid=group_1.id.hex)
        form.on_request()


def test_daily_list_selection_form(session):
    form = DailyListSelectionForm()
    form.request = Request(session)

    # Test get model
    form.date.data = date(2019, 1, 1)
    form.type.data = 'boxes'
    model = form.get_model()
    assert model.__class__.__name__ == 'DailyListBoxes'
    assert model.date == date(2019, 1, 1)


def test_report_selection_form(session):
    groups = UserGroupCollection(session)
    municipalities = MunicipalityCollection(session)
    municipalities.add(
        name="Adlikon",
        bfs_number=21,
        group_id=groups.add(name="Winterthur").id
    )
    municipalities.add(
        name="Aesch",
        bfs_number=241,
        group_id=groups.add(name="Aesch").id
    )

    # Test choices
    form = ReportSelectionForm()
    form.request = Request(session)
    form.on_request()
    assert form.municipality.choices == [
        ('Adlikon', 'Adlikon'),
        ('Aesch', 'Aesch')
    ]

    # Test get model
    form.start.data = date(2019, 1, 1)
    form.end.data = date(2019, 1, 31)
    form.scan_job_type.data = 'express'
    form.municipality.data = 'Aesch'

    form.report_type.data = 'boxes'
    model = form.get_model()
    assert model.__class__.__name__ == 'ReportBoxes'
    assert model.start == date(2019, 1, 1)
    assert model.end == date(2019, 1, 31)

    form.report_type.data = 'boxes_and_forms'
    model = form.get_model()
    assert model.__class__.__name__ == 'ReportBoxesAndForms'
    assert model.start == date(2019, 1, 1)
    assert model.end == date(2019, 1, 31)
    assert model.type == 'express'

    form.report_type.data = 'forms'
    model = form.get_model()
    assert model.__class__.__name__ == 'ReportFormsByMunicipality'
    assert model.start == date(2019, 1, 1)
    assert model.end == date(2019, 1, 31)
    assert model.type == 'express'
    assert model.municipality == 'Aesch'
