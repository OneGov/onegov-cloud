from cgi import FieldStorage
from datetime import date
from freezegun import freeze_time
from io import BytesIO
from mock import MagicMock
from onegov.core.utils import module_path
from onegov.user import User
from onegov.user import UserCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.forms import AddScanJobForm
from onegov.wtfs.forms import CreateInvoicesForm
from onegov.wtfs.forms import DailyListSelectionForm
from onegov.wtfs.forms import DeleteMunicipalityDatesForm
from onegov.wtfs.forms import EditScanJobForm
from onegov.wtfs.forms import ImportMunicipalityDataForm
from onegov.wtfs.forms import MunicipalityForm
from onegov.wtfs.forms import MunicipalityIdSelectionForm
from onegov.wtfs.forms import NotificationForm
from onegov.wtfs.forms import PaymentTypesForm
from onegov.wtfs.forms import ReportSelectionForm
from onegov.wtfs.forms import ScanJobsForm
from onegov.wtfs.forms import UnrestrictedScanJobForm
from onegov.wtfs.forms import UnrestrictedScanJobsForm
from onegov.wtfs.forms import UnrestrictedUserForm
from onegov.wtfs.forms import UserForm
from onegov.wtfs.forms import UserManualForm
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Notification
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import ScanJob
from onegov.wtfs.models import UserManual
from pytest import mark


class App(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class Identity(object):
    def __init__(self, groupid, userid=None, role=None):
        self.groupid = groupid
        self.userid = userid


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


def test_payments_form(session):
    model = PaymentTypeCollection(session)
    request = Request(session)

    form = PaymentTypesForm.get_form_class(model, request)()
    assert [field for field in form] == []

    model.add(name='normal', _price_per_quantity=700)
    model.add(name='spezial', _price_per_quantity=850)
    form = PaymentTypesForm.get_form_class(model, request)()
    assert [(field.name, field.type) for field in form] == [
        ('normal', 'FloatField'), ('spezial', 'FloatField')
    ]

    # Test apply / update
    form.apply_model(model)
    assert form.normal.data == 7.0
    assert form.spezial.data == 8.5

    form.normal.data = 8.0
    form.spezial.data = 9

    form.update_model(model)
    assert {r.name: r.price_per_quantity for r in model.query()} == {
        'normal': 8.0, 'spezial': 9.0
    }

    # Test validation
    form = PaymentTypesForm.get_form_class(model, request)(
        PostData({
            'normal': 10.0,
            'spezial': 12.6,
        })
    )
    form.request = Request(session)
    assert form.validate()


def test_municipality_form(session):
    payment_types = PaymentTypeCollection(session)
    payment_types.add(name='normal', _price_per_quantity=700)
    payment_types.add(name='spezial', _price_per_quantity=850)

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(
        name="Boppelsen",
        bfs_number=82,
        payment_type='normal'
    )

    # Test choices
    form = MunicipalityForm()
    form.request = Request(session)
    form.on_request()
    assert form.payment_type.choices == [
        ('normal', 'Normal'), ('spezial', 'Spezial')
    ]

    # Test apply / update
    form.apply_model(municipality)
    assert form.name.data == "Boppelsen"
    assert form.bfs_number.data == 82
    assert form.address_supplement.data is None
    assert form.gpn_number.data is None
    assert form.payment_type.data == 'normal'

    form.name.data = "Adlikon"
    form.bfs_number.data = 21
    form.address_supplement.data = "Zusatz"
    form.gpn_number.data = 1122
    form.payment_type.data = 'spezial'

    form.update_model(municipality)
    assert municipality.name == "Adlikon"
    assert municipality.bfs_number == 21
    assert municipality.address_supplement == "Zusatz"
    assert municipality.gpn_number == 1122
    assert municipality.payment_type == 'spezial'

    # Test validation
    form = MunicipalityForm()
    form.request = Request(session)
    form.on_request()
    assert not form.validate()

    form = MunicipalityForm(
        PostData({
            'bfs_number': '82',
        })
    )
    form.request = Request(session)
    form.on_request()
    assert not form.validate()

    form = MunicipalityForm(
        PostData({
            'name': "Boppelsen",
            'bfs_number': '82',
            'payment_type': 'normal'
        })
    )
    form.request = Request(session)
    form.on_request()
    assert form.validate()


def test_import_municipality_data_form(session):
    municipalities = MunicipalityCollection(session)
    municipalities.add(name="Boppelsen", bfs_number=82)
    municipalities.add(name="Adlikon", bfs_number=21)

    # Test apply
    form = ImportMunicipalityDataForm()
    form.request = Request(session)

    form.file.data = {
        21: {'dates': [date(2019, 1, 1), date(2019, 1, 7)]},
        241: {'dates': [date(2019, 1, 3), date(2019, 1, 9)]},
        82: {'dates': [date(2019, 1, 4), date(2019, 1, 10)]}
    }
    form.update_model(municipalities)
    assert [
        (m.bfs_number, [d.date for d in m.pickup_dates])
        for m in municipalities.query()
    ] == [
        (21, [date(2019, 1, 1), date(2019, 1, 7)]),
        (82, [date(2019, 1, 4), date(2019, 1, 10)])
    ]

    # Test validation
    form = ImportMunicipalityDataForm()
    form.request = Request(session)
    assert not form.validate()

    field_storage = FieldStorage()
    field_storage.file = BytesIO(
        "Adlikon;21;-1;Normal;12.2.2015".encode('cp1252')
    )
    field_storage.type = 'text/csv'
    field_storage.filename = 'test.csv'
    form.file.process(PostData({'file': field_storage}))

    assert form.validate()


def test_delete_municipality_dates_form(session):
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name="Boppelsen", bfs_number=82)

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

    with freeze_time("2018-01-05"):
        form.apply_model(municipality)
        assert form.start.data == date(2018, 12, 31)
        assert form.end.data == date(2020, 1, 1)

    with freeze_time("2019-01-05"):
        form.apply_model(municipality)
        assert form.start.data == date(2019, 1, 1)
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
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name="Aesch", bfs_number=82)

    # Test choices
    form = MunicipalityIdSelectionForm()
    form.request = Request(session)
    form.on_request()
    assert [c[1] for c in form.municipality_id.choices] == ["Aesch"]

    form.municipality_id.data = municipality.id
    assert form.municipality == municipality


def test_user_form(session):
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name="Aesch", bfs_number=82)

    # Test apply / update
    form = UserForm()
    form.request = Request(session, groupid=municipality.id.hex)

    user = User()
    form.realname.data = "Petra Muster"
    form.username.data = "petra.muster@winterthur.ch"
    form.contact.data = False
    form.update_model(user)
    assert user.realname == "Petra Muster"
    assert user.username == "petra.muster@winterthur.ch"
    assert user.group_id == municipality.id.hex
    assert user.role == 'member'
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
    assert user.group_id == municipality.id.hex
    assert user.role == 'member'
    assert user.data['contact'] is True
    assert user.password_hash == password_hash
    assert user.logout_all_sessions.called is True

    form.request.identity.userid = "hans-peter.muster@winterthur.ch"
    form.request.identity.role = 'editor'
    form.update_model(user)
    assert user.realname == "Hans-Peter Muster"
    assert user.username == "hans-peter.muster@winterthur.ch"
    assert user.group_id == municipality.id.hex
    assert user.role == 'editor'
    assert user.data['contact'] is True
    assert user.password_hash == password_hash
    assert user.logout_all_sessions.called is True

    # Test validation
    form = UserForm()
    form.request = Request(session, groupid=municipality.id.hex)
    assert not form.validate()

    form = UserForm(PostData({
        'realname': "Hans-Peter Muster",
        'username': "hans-peter.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=municipality.id.hex)
    assert not form.validate()
    assert form.errors == {'username': ['This value already exists.']}

    form = UserForm(PostData({
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=municipality.id.hex)
    assert form.validate()


def test_unrestricted_user_form(session):
    municipalities = MunicipalityCollection(session)
    municipality_1 = municipalities.add(name="Aesch", bfs_number=82)
    municipality_2 = municipalities.add(name="Adlikon", bfs_number=21)

    # Test choices
    form = UnrestrictedUserForm()
    form.request = Request(session)
    form.on_request()
    assert [c[1] for c in form.municipality_id.choices] == [
        "- none -", "Adlikon (21)", "Aesch (82)"
    ]
    assert form.role.choices == [
        ('admin', "Admin"),
        ('editor', "Editor"),
        ('member', "Member")
    ]

    # Test apply / update
    user = User()
    form.role.data = "member"
    form.municipality_id.data = None
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
    user.group_id = municipality_1.id
    user.logout_all_sessions = MagicMock()
    password_hash = user.password_hash

    form.apply_model(user)
    assert form.role.data == 'member'
    assert form.municipality_id.data == municipality_1.id.hex
    assert form.realname.data == "Hans Muster"
    assert form.username.data == "hans.muster@winterthur.ch"
    assert form.contact.data is False

    form.role.data = 'admin'
    form.municipality_id.data = municipality_2.id.hex
    form.realname.data = "Hans-Peter Muster"
    form.username.data = "hans-peter.muster@winterthur.ch"
    form.contact.data = True
    form.update_model(user)
    assert user.realname == "Hans-Peter Muster"
    assert user.username == "hans-peter.muster@winterthur.ch"
    assert user.group_id == municipality_2.id.hex
    assert user.data['contact'] is True
    assert user.password_hash == password_hash
    assert user.logout_all_sessions.called is True

    # Test validation
    form = UnrestrictedUserForm()
    form.request = Request(session, groupid=municipality_1.id.hex)
    form.on_request()
    assert not form.validate()

    form = UnrestrictedUserForm(PostData({
        'role': 'member',
        'realname': "Hans-Peter Muster",
        'username': "hans-peter.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=municipality_1.id.hex)
    form.on_request()
    assert not form.validate()
    assert form.errors == {'username': ['This value already exists.']}

    form = UnrestrictedUserForm(PostData({
        'role': 'member',
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=municipality_1.id.hex)
    form.on_request()
    assert form.validate()

    form = UnrestrictedUserForm(PostData({
        'role': 'editor',
        'municipality_id': municipality_2.id.hex,
        'realname': "Hans Muster",
        'username': "hans.muster@winterthur.ch"
    }))
    form.request = Request(session, groupid=municipality_1.id.hex)
    form.on_request()
    assert form.validate()


def test_add_scan_job_form(session):
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name="Boppelsen", bfs_number=82)
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 1)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 15)))

    # Test on request
    form = AddScanJobForm()
    form.request = Request(session, groupid=municipality.id.hex)
    assert form.municipality_id == municipality.id.hex
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [('normal', 'Regular shipment')]
        assert form.dispatch_date_normal.choices == [
            (date(2019, 1, 8), '08.01.2019'),
            (date(2019, 1, 15), '15.01.2019')
        ]
    form.request = Request(session, groupid=municipality.id.hex,
                           roles=['editor'])
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [
            ('normal', 'Regular shipment'),
            ('express', 'Express shipment')
        ]
        assert form.dispatch_date_normal.choices == [
            (date(2019, 1, 8), '08.01.2019'),
            (date(2019, 1, 15), '15.01.2019')
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
    assert model.municipality_id == municipality.id.hex
    assert model.type == 'normal'
    assert model.dispatch_date == date(2019, 1, 8)
    assert model.return_date == date(2019, 1, 15)
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
    assert model.return_date == date(2019, 1, 8)

    # Test validation
    with freeze_time("2019-01-05"):
        form = AddScanJobForm()
        form.request = Request(session, groupid=municipality.id.hex)
        form.on_request()
        assert not form.validate()

        form = AddScanJobForm(PostData({
            'municipality_id': municipality.id.hex,
            'type': 'normal',
            'dispatch_date_normal': '2019-01-08'
        }))
        form.request = Request(session, groupid=municipality.id.hex)
        form.on_request()
        assert form.validate()


def test_edit_scan_job_form(session):
    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name="Boppelsen", bfs_number=82)
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    # Test apply / update
    model = ScanJob()
    model.municipality_id = municipality.id
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

    form = EditScanJobForm()
    form.request = Request(session, groupid=municipality.id.hex)
    form.apply_model(model)
    assert form.dispatch_boxes.data == 1
    assert form.dispatch_tax_forms_current_year.data == 2
    assert form.dispatch_tax_forms_last_year.data == 3
    assert form.dispatch_tax_forms_older.data == 4
    assert form.dispatch_single_documents.data == 5
    assert form.dispatch_note.data == 'Note on dispatch'
    assert form.dispatch_cantonal_tax_office.data == 6
    assert form.dispatch_cantonal_scan_center.data == 7

    form.dispatch_boxes.data = 10
    form.dispatch_tax_forms_current_year.data = 20
    form.dispatch_tax_forms_last_year.data = 30
    form.dispatch_tax_forms_older.data = 40
    form.dispatch_single_documents.data = 50
    form.dispatch_note.data = 'A note on the dispatch'
    form.dispatch_cantonal_tax_office.data = 60
    form.dispatch_cantonal_scan_center.data = 70

    form.update_model(model)
    assert model.municipality_id == municipality.id
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

    # Test validation
    form = EditScanJobForm()
    form.request = Request(session, groupid=municipality.id.hex)
    assert form.validate()


def test_unrestricted_scan_job_form(session):
    municipalities = MunicipalityCollection(session)
    municipality_1 = municipalities.add(name="Boppelsen", bfs_number=82)
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 7)))
    municipality_1.pickup_dates.append(PickupDate(date=date(2019, 1, 8)))

    municipality_2 = municipalities.add(name="Adlikon", bfs_number=21)
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 17)))
    municipality_2.pickup_dates.append(PickupDate(date=date(2019, 1, 18)))

    # Test on request
    form = UnrestrictedScanJobForm()
    form.request = Request(session, groupid=municipality_1.id.hex)
    with freeze_time("2019-01-05"):
        form.on_request()
        assert form.type.choices == [
            ('normal', 'Regular shipment'),
            ('express', 'Express shipment')
        ]
        assert form.municipality_id.choices == [
            (municipality_2.id.hex, 'Adlikon (21)'),
            (municipality_1.id.hex, 'Boppelsen (82)')
        ]

    # Test apply / update
    model = ScanJob()
    model.municipality_id = municipality_1.id
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
    model.return_tax_forms_current_year = 9
    model.return_tax_forms_last_year = 10
    model.return_tax_forms_older = 11
    model.return_single_documents = 12
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
    assert form.return_tax_forms_current_year.data == 9
    assert form.return_tax_forms_last_year.data == 10
    assert form.return_tax_forms_older.data == 11
    assert form.return_single_documents.data == 12
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
    form.return_tax_forms_current_year.data = 90
    form.return_tax_forms_last_year.data = 100
    form.return_tax_forms_older.data = 110
    form.return_single_documents.data = 120
    form.return_unscanned_tax_forms_current_year.data = 130
    form.return_unscanned_tax_forms_last_year.data = 140
    form.return_unscanned_tax_forms_older.data = 150
    form.return_unscanned_single_documents.data = 160
    form.return_note.data = 'A note on the return'

    form.update_model(model)
    assert model.municipality_id == municipality_2.id.hex
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
    assert model.return_tax_forms_current_year == 90
    assert model.return_tax_forms_last_year == 100
    assert model.return_tax_forms_older == 110
    assert model.return_single_documents == 120
    assert model.return_unscanned_tax_forms_current_year == 130
    assert model.return_unscanned_tax_forms_last_year == 140
    assert model.return_unscanned_tax_forms_older == 150
    assert model.return_unscanned_single_documents == 160
    assert model.return_note == 'A note on the return'

    # Test validation
    with freeze_time("2019-01-05"):
        form = UnrestrictedScanJobForm()
        form.request = Request(session, groupid=municipality_1.id.hex)
        form.on_request()
        assert not form.validate()

        form = UnrestrictedScanJobForm(PostData({
            'municipality_id': municipality_1.id.hex,
            'type': 'normal',
            'dispatch_date': '2019-01-18'
        }))
        form.request = Request(session, groupid=municipality_1.id.hex)
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

    # Test get model
    form.date.data = date(2019, 1, 1)
    form.type.data = 'boxes_and_forms'
    model = form.get_model()
    assert model.__class__.__name__ == 'DailyListBoxesAndForms'
    assert model.date == date(2019, 1, 1)


def test_report_selection_form(session):
    municipalities = MunicipalityCollection(session)
    adlikon = municipalities.add(name="Adlikon", bfs_number=21)
    aesch = municipalities.add(name="Aesch", bfs_number=241)

    # Test choices
    form = ReportSelectionForm()
    form.request = Request(session)
    form.on_request()
    assert form.municipality_id.choices == [
        (adlikon.id.hex, 'Adlikon (21)'),
        (aesch.id.hex, 'Aesch (241)')
    ]

    # Test get model
    form.start.data = date(2019, 1, 1)
    form.end.data = date(2019, 1, 31)
    form.scan_job_type.data = 'express'
    form.municipality_id.data = aesch.id.hex

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
    assert model.municipality_id == aesch.id.hex

    form.report_type.data = 'delivery'
    model = form.get_model()
    assert model.__class__.__name__ == 'ReportBoxesAndFormsByDelivery'
    assert model.start == date(2019, 1, 1)
    assert model.end == date(2019, 1, 31)
    assert model.type == 'express'
    assert model.municipality_id == aesch.id.hex


def test_notification_form():
    # Test apply / update
    form = NotificationForm()
    notification = Notification(title="Title", text="Text")

    form.apply_model(notification)
    assert form.title.data == "Title"
    assert form.text.data == "Text"

    form.title.data = "Title"
    form.text.data = "Text"
    form.update_model(notification)
    assert notification.title == "Title"
    assert notification.text == "Text"

    # Test validation
    form = NotificationForm()
    assert not form.validate()

    form = NotificationForm(PostData({
        'title': "Title",
        'text': "Text"
    }))
    assert form.validate()


def test_scan_jobs_form(session):
    scan_jobs = ScanJobCollection(session)

    # Test apply
    form = ScanJobsForm()
    form.apply_model(scan_jobs)
    assert form.sort_by.data is None
    assert form.sort_order.data is None
    assert form.from_date.data is None
    assert form.to_date.data is None
    assert form.type.data == ['normal', 'express']
    assert form.term.data is None

    scan_jobs.sort_by = 'delivery_number'
    scan_jobs.sort_order = 'ascending'
    scan_jobs.from_date = date(2010, 1, 1)
    scan_jobs.to_date = date(2010, 12, 31)
    scan_jobs.type = ['express']
    scan_jobs.term = 'term'

    form.apply_model(scan_jobs)

    assert form.sort_by.data == 'delivery_number'
    assert form.sort_order.data == 'ascending'
    assert form.from_date.data == date(2010, 1, 1)
    assert form.to_date.data == date(2010, 12, 31)
    assert form.type.data == ['express']
    assert form.term.data == 'term'

    # Test validation
    form = ScanJobsForm()
    assert form.validate()


def test_unrestricted_scan_jobs_form(session):
    scan_jobs = ScanJobCollection(session)
    municipalities = MunicipalityCollection(session)
    municipalities.add(name="Adlikon", bfs_number=21)
    municipalities.add(name="Aesch", bfs_number=241)

    # Test on request / popluate
    form = UnrestrictedScanJobsForm()
    form.request = Request(session)
    form.on_request()
    assert [m[1] for m in form.municipality_id.choices] == [
        'Adlikon (21)',
        'Aesch (241)'
    ]

    # Test apply
    form.apply_model(scan_jobs)
    assert form.sort_by.data is None
    assert form.sort_order.data is None
    assert form.from_date.data is None
    assert form.to_date.data is None
    assert form.type.data == ['normal', 'express']
    assert form.municipality_id.data is None
    assert form.term.data is None

    scan_jobs.sort_by = 'delivery_number'
    scan_jobs.sort_order = 'ascending'
    scan_jobs.from_date = date(2010, 1, 1)
    scan_jobs.to_date = date(2010, 12, 31)
    scan_jobs.type = ['express']
    scan_jobs.term = 'term'
    scan_jobs.municipality_id = [municipalities.query().first().id]

    form.apply_model(scan_jobs)

    assert form.sort_by.data == 'delivery_number'
    assert form.sort_order.data == 'ascending'
    assert form.from_date.data == date(2010, 1, 1)
    assert form.to_date.data == date(2010, 12, 31)
    assert form.type.data == ['express']
    assert form.term.data == 'term'
    assert form.municipality_id.data == [municipalities.query().first().id]

    # Test validation
    form = UnrestrictedScanJobsForm()
    assert form.validate()


def test_create_invoices_form(session):
    municipalities = MunicipalityCollection(session)
    adlikon = municipalities.add(name="Adlikon", bfs_number=21)
    aesch = municipalities.add(name="Aesch", bfs_number=241)

    # Test choices
    form = CreateInvoicesForm()
    form.request = Request(session)
    form.on_request()
    assert form.municipality_id.choices == [
        ('-', 'For all municipalities'),
        (adlikon.id.hex, 'Adlikon (21)'),
        (aesch.id.hex, 'Aesch (241)')
    ]

    # Test update model
    form.from_date.data = date(2019, 1, 1)
    form.to_date.data = date(2019, 1, 31)
    form.cs2_user.data = '123456'
    form.subject.data = 'Rechnungen'
    form.municipality_id.data = aesch.id.hex
    form.accounting_unit.data = '99999'
    form.revenue_account.data = '987654321'

    model = Invoice(session)
    form.update_model(model)
    assert model.from_date == date(2019, 1, 1)
    assert model.to_date == date(2019, 1, 31)
    assert model.cs2_user == '123456'
    assert model.subject == 'Rechnungen'
    assert model.municipality_id == aesch.id.hex
    assert model.accounting_unit == '99999'
    assert model.revenue_account == '987654321'

    form.municipality_id.data = '-'
    form.update_model(model)
    assert model.municipality_id is None


@mark.parametrize("pdf_1, pdf_2", [(
    module_path('onegov.wtfs', 'tests/fixtures/example_1.pdf'),
    module_path('onegov.wtfs', 'tests/fixtures/example_2.pdf')
)])
def test_user_manual_form(wtfs_app, pdf_1, pdf_2):
    with open(pdf_1, 'rb') as file:
        pdf_1 = BytesIO(file.read())
    with open(pdf_2, 'rb') as file:
        pdf_2 = BytesIO(file.read())

    user_manual = UserManual(wtfs_app)

    form = UserManualForm()
    form.apply_model(user_manual)
    assert form.pdf.data is None

    # Add
    field_storage = FieldStorage()
    field_storage.file = pdf_1
    field_storage.type = 'application/pdf'
    field_storage.filename = 'example_1.pdf'
    form.pdf.process(PostData({'pdf': field_storage}))
    form.update_model(user_manual)
    pdf_1.seek(0)
    assert user_manual.pdf == pdf_1.read()
    form.apply_model(user_manual)
    assert form.pdf.data == {
        'filename': 'user_manual.pdf',
        'size': 8130,
        'mimetype': 'application/pdf'
    }

    # Replace
    field_storage = FieldStorage()
    field_storage.file = pdf_2
    field_storage.type = 'application/pdf'
    field_storage.filename = 'example_2.pdf'
    form.pdf.process(PostData({'pdf': field_storage}))
    form.update_model(user_manual)
    pdf_2.seek(0)
    assert user_manual.pdf == pdf_2.read()
    form.apply_model(user_manual)
    assert form.pdf.data == {
        'filename': 'user_manual.pdf',
        'size': 9115,
        'mimetype': 'application/pdf'
    }

    # Delete
    form.pdf.action = 'delete'
    form.update_model(user_manual)
    assert not user_manual.exists
