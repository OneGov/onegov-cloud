from __future__ import annotations

from cgi import FieldStorage
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.forms import AgencyMutationForm
from onegov.agency.forms import ApplyMutationForm
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.forms import MembershipForm
from onegov.agency.forms import MoveAgencyForm
from onegov.agency.forms import PersonMutationForm
from onegov.agency.forms import UserGroupForm
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.core.utils import Bunch
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from tempfile import TemporaryFile
from tests.shared.utils import encode_map_value
from unittest.mock import MagicMock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency import AgencyApp
    from onegov.agency.request import AgencyRequest as BaseRequest
    from onegov.user import User
    from sqlalchemy.orm import Session
    from webob.multidict import MultiDict

    BasePostData = MultiDict[str, Any]
else:
    BaseRequest = object
    BasePostData = dict


class DummyApp:
    def __init__(self, session: Session, principal: object) -> None:
        self._session = session

    def session(self) -> Session:
        return self._session


class DummyRequest(BaseRequest):
    def __init__(
        self,
        session: Session,
        principal: object = None,
        private: bool = False,
        secret: bool = False,
        permissions: dict[str, list[str]] | None = None,
        current_user: User | None = None
    ) -> None:
        self.app = DummyApp(session, principal)  # type: ignore[assignment]
        self.session = session
        self.private = private
        self.secret = secret
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'
        self.permissions = permissions or {}
        self.current_user = current_user  # type: ignore[misc]
        self.client_addr = '1.1.1.1'  # type: ignore[misc]

    def is_private(self, model: object) -> bool:
        return self.private

    def is_secret(self, model: object) -> bool:
        return self.secret

    def include(self, resource: object) -> None:
        pass

    def translate(self, text: str) -> str:  # type: ignore[override]
        return text.interpolate() if hasattr(text, 'interpolate') else text

    def has_permission(self, model: object, permission: type[object]) -> bool:  # type: ignore[override]
        permissions = self.permissions.get(model.__class__.__name__, [])
        return permission.__name__ in permissions


class DummyPostData(BasePostData):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def create_file(mimetype: str, filename: str, content: bytes) -> FieldStorage:
    fs = FieldStorage()
    fs.file = TemporaryFile("wb+")
    fs.type = mimetype
    fs.filename = filename
    fs.file.write(content)
    fs.file.seek(0)
    return fs


def test_extended_agency_form(agency_app: AgencyApp) -> None:
    # get useful data
    form = ExtendedAgencyForm(DummyPostData({
        'title': 'Springfield Hospital',
        'portrait': 'Springfield Hospital is hospital.',
        'location_address': 'Springfield Lane\n12345 Springfield',
        'postal_address': 'Hospital Blvd\nPostbox',
        'postal_code_city': '12345 Hospital City',
        'phone': '+1 23456789',
        'phone_direct': '+1 98765432',
        'email': 'emc@springfieldhospital.com',
        'website': 'springfieldhospital.com',
        'opening_hours': 'Mo bis Mittwoch\n8.00 - 8.01',
        'coordinates': encode_map_value({'lat': 1, 'lon': 2, 'zoom': 12}),
        'export_fields': ['person.first_name', 'person.last_name'],
        'organigram': create_file('image/png', 'org.png', b'PNG',),
    }))
    data = form.get_useful_data()
    assert list(data.keys()) == [
        'title', 'portrait', 'location_address', 'location_code_city',
        'postal_address', 'postal_code_city', 'phone', 'phone_direct',
        'email', 'website', 'opening_hours', 'coordinates', 'export_fields',
        'organigram_file'
    ]
    assert data['organigram_file'].read() == b'PNG'
    assert data['title'] == 'Springfield Hospital'
    assert data['portrait'] == 'Springfield Hospital is hospital.'
    assert data['location_address'] == 'Springfield Lane\n12345 Springfield'
    assert data['postal_address'] == 'Hospital Blvd\nPostbox'
    assert data['postal_code_city'] == '12345 Hospital City'
    assert data['phone'] == '+1 23456789'
    assert data['phone_direct'] == '+1 98765432'
    assert data['email'] == 'emc@springfieldhospital.com'
    assert data['website'] == 'http://springfieldhospital.com'
    assert data['opening_hours'] == 'Mo bis Mittwoch\n8.00 - 8.01'
    coordinates = data['coordinates']
    assert coordinates.lat == 1
    assert coordinates.lon == 2
    assert coordinates.zoom == 12
    assert data['export_fields'] == ['person.first_name', 'person.last_name']

    # update / apply / reorder
    model = ExtendedAgency(title='dummy')

    form.update_model(model)
    assert model.title == 'Springfield Hospital'
    assert model.portrait == 'Springfield Hospital is hospital.'
    assert model.export_fields == ['person.first_name', 'person.last_name']
    assert model.organigram_file.read() == b'PNG'  # type: ignore[union-attr]

    form = ExtendedAgencyForm()
    form.apply_model(model)
    assert form.title.data == 'Springfield Hospital'
    assert form.portrait.data == 'Springfield Hospital is hospital.'
    assert form.export_fields.data == ['person.first_name', 'person.last_name']
    assert form.export_fields.choices[:2] == [  # type: ignore[index]
        ('person.first_name', 'Person: First Name'),
        ('person.last_name', 'Person: Last Name')
    ]
    assert form.organigram.data['size']  # type: ignore[index]


def test_extended_agency_form_choices() -> None:
    models = {
        'membership': ExtendedAgencyMembership(),
        'person': ExtendedPerson(first_name="f", last_name="l")
    }

    form = ExtendedAgencyForm()
    for choice in form.export_fields.choices:
        model, attribute = choice[0].split('.')
        assert hasattr(models[model], attribute)


def test_move_agency_form(session: Session) -> None:
    all_permissions = {
        'ExtendedAgency': ['Private'],
        'ExtendedAgencyCollection': ['Private']
    }

    agencies = ExtendedAgencyCollection(session)
    agency_a = agencies.add_root(title="a")
    agencies.add(title="a.1", parent=agency_a)
    agency_a_2 = agencies.add(title="a.2", parent=agency_a)
    agency_a_2_1 = agencies.add(title="a.2.1", parent=agency_a_2)
    agency_f = agencies.add_root(title="f")
    agencies.add_root(title="ç")

    # request
    form = MoveAgencyForm()

    form.request = DummyRequest(session)
    form.on_request()
    assert form.parent_id.choices == []

    form.request = DummyRequest(session, permissions={
        'ExtendedAgency': ['Private']
    })
    form.on_request()
    assert form.parent_id.choices == [
        ('1', 'a'), ('2', 'a.1'), ('3', 'a.2'), ('4', 'a.2.1'),
        ('6', 'ç'), ('5', 'f')
    ]

    form.request = DummyRequest(session, permissions={
        'ExtendedAgencyCollection': ['Private']
    })
    form.on_request()
    assert form.parent_id.choices == [
        ('root', '- Root -'),
    ]

    form.request = DummyRequest(session, permissions=all_permissions)
    form.on_request()
    assert form.parent_id.choices == [
        ('root', '- Root -'),
        ('1', 'a'), ('2', 'a.1'), ('3', 'a.2'), ('4', 'a.2.1'),
        ('6', 'ç'), ('5', 'f')
    ]

    # apply
    form.apply_model(agency_a)
    assert form.parent_id.choices == [
        ('6', 'ç'), ('5', 'f')
    ]

    form.on_request()
    form.apply_model(agency_a_2)
    assert form.parent_id.choices == [
        ('root', '- Root -'),
        ('2', 'a.1'),
        ('6', 'ç'), ('5', 'f')
    ]

    form.on_request()
    form.apply_model(agency_a_2_1)
    assert form.parent_id.choices == [
        ('root', '- Root -'),
        ('1', 'a'), ('2', 'a.1'),
        ('6', 'ç'), ('5', 'f')
    ]

    form.on_request()
    form.apply_model(agency_f)
    assert form.parent_id.choices == [
        ('1', 'a'), ('2', 'a.1'), ('3', 'a.2'), ('4', 'a.2.1'),
        ('6', 'ç')
    ]

    # update
    model = ExtendedAgency(title="Agency")
    form = MoveAgencyForm()
    form.request = DummyRequest(session, permissions=all_permissions)
    form.update_model(model)
    assert model.parent_id == None

    form = MoveAgencyForm(DummyPostData({'parent_id': 'root'}))
    form.request = DummyRequest(session, permissions=all_permissions)
    form.update_model(model)
    assert model.parent_id == None

    form = MoveAgencyForm(DummyPostData({'parent_id': '10'}))
    form.request = DummyRequest(session, permissions=all_permissions)
    form.update_model(model)
    assert model.parent_id == 10

    # update with rename
    agency_a_2_2 = agencies.add(title="a.2", parent=agency_a_2)
    form = MoveAgencyForm(DummyPostData({'parent_id': agency_a_2.parent_id}))
    form.request = DummyRequest(session, permissions=all_permissions)
    form.update_model(agency_a_2_2)
    session.flush()


def test_membership_form(session: Session) -> None:
    people = ExtendedPersonCollection(session)
    request = DummyRequest(session)

    doctor = people.add(first_name="Nick", last_name="Rivera")

    form = MembershipForm()
    form.request = request
    form.on_request()
    assert form.person_id.choices == [(str(doctor.id), 'Rivera Nick')]

    form = MembershipForm(DummyPostData({
        'person_id': str(doctor.id),
        'title': "Doctor",
        'since': "2000",
        'addition': "Surgery",
        'note': "Retired",
        'prefix': "*",
    }))
    assert form.get_useful_data() == {
        'person_id': str(doctor.id),
        'title': "Doctor",
        'addition': "Surgery",
        'note': "Retired",
        'since': "2000",
        'prefix': "*",
    }


def test_membership_form_choices(session: Session) -> None:
    people = ExtendedPersonCollection(session)
    people.add(first_name="Nick", last_name="Rivera")
    people.add(first_name="Nick", last_name="Rivera", phone="1234")
    people.add(first_name="Nick", last_name="Rivera", phone="5555", email="x")
    people.add(first_name="Nick", last_name="Rivera", phone_direct="4")
    people.add(first_name="Nick", last_name="Rivera", postal_address="Street",
               postal_code_city="9876 Telltown")
    people.add(first_name="Nick", last_name="Rivera", email="n@h.com")

    agencies = ExtendedAgencyCollection(session)
    agency = agencies.add_root(title="Hospital")
    doc = people.add(first_name="Nick", last_name="Rivera")
    agency.add_person(doc.id, "Doc")

    request = DummyRequest(session)
    form = MembershipForm()
    form.request = request
    form.on_request()

    assert sorted([x[1] for x in form.person_id.choices]) == [
        'Rivera Nick',
        'Rivera Nick (1234)',
        'Rivera Nick (4)',
        'Rivera Nick (5555)',
        'Rivera Nick (Hospital)',
        'Rivera Nick (Street)',
        'Rivera Nick (n@h.com)'
    ]


def test_agency_mutation_form() -> None:
    form = AgencyMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'title': 'Hospital Springfield',
        'location_address': '',
        'location_code_city': '',
        'postal_address': '',
        'postal_code_city': '',
        'phone': '',
        'phone_direct': '',
        'email': '',
        'website': '',
        'opening_hours': '',
    }))
    form.model = ExtendedAgency(title='Hopital Springfield',
                                email='info@abc.com')
    form.request = DummyRequest(None)  # type: ignore[arg-type]
    form.on_request()

    assert set(form.proposal_fields.keys()) == {
        'title', 'location_address', 'location_code_city', 'postal_address',
        'postal_code_city', 'phone', 'phone_direct', 'email', 'website',
        'opening_hours'}
    assert form.title.description == 'Hopital Springfield'
    assert form.proposed_changes == {'title': 'Hospital Springfield'}
    assert form.get_useful_data() == {
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'title': 'Hospital Springfield',
        'location_address': '',
        'location_code_city': '',
        'postal_address': '',
        'postal_code_city': '',
        'phone': '',
        'phone_direct': '',
        'email': '',
        'website': '',
        'opening_hours': '',
    }
    assert form.validate()

    # No content
    form = AgencyMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
    }))
    assert not form.validate()

    # Honeypot
    form = AgencyMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': "Nick Rivera's retired.",
        'delay': '10'
    }))
    form.request = DummyRequest(None)  # type: ignore[arg-type]
    assert not form.validate()


def test_person_mutation_form() -> None:
    form = PersonMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'first_name': 'nick',
        'last_name': 'Rivera',
        'academic_title': 'Dr.',
    }))
    form.model = ExtendedPerson(first_name="Nick", last_name="Riviera")
    form.request = DummyRequest(None)  # type: ignore[arg-type]
    form.on_request()

    assert set(form.proposal_fields.keys()) == {
        'function', 'website', 'website_2', 'political_party', 'salutation',
        'email', 'notes', 'first_name', 'last_name', 'born', 'phone',
        'parliamentary_group', 'location_address',
        'location_code_city', 'postal_address', 'postal_code_city',
        'profession', 'phone_direct', 'academic_title'
    }
    assert form.first_name.description == 'Nick'
    assert form.last_name.description == 'Riviera'
    assert form.academic_title.description is None
    assert form.proposed_changes == {
        'academic_title': 'Dr.', 'first_name': 'nick', 'last_name': 'Rivera'
    }
    assert form.get_useful_data() == {
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'salutation': None,
        'academic_title': 'Dr.',
        'first_name': 'nick',
        'last_name': 'Rivera',
        'function': None,
        'email': None,
        'phone': None,
        'phone_direct': None,
        'born': None,
        'profession': None,
        'political_party': None,
        'parliamentary_group': None,
        'website': None,
        'website_2': None,
        'location_address': None,
        'location_code_city': None,
        'postal_address': None,
        'postal_code_city': None,
        'notes': None
    }
    assert form.validate()

    # No content
    form = PersonMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
    }))
    assert not form.validate()

    # Honeypot
    form = PersonMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': "Nick Rivera's retired.",
        'delay': '10'
    }))
    form.request = DummyRequest(None)  # type: ignore[arg-type]
    assert not form.validate()


def test_apply_muation_form() -> None:
    form = ApplyMutationForm(DummyPostData({'changes': ['a', 'b']}))
    form.request = DummyRequest(None)  # type: ignore[arg-type]
    form.model = Bunch(
        labels={'a': 'A', 'c': 'C'},
        changes={'a': 'X', 'b': 'Y', 'c': 'Z'},
        apply=MagicMock()
    )
    form.on_request()
    assert form.changes.choices == [
        ('a', 'A: X'), ('b', 'b: Y'), ('c', 'C: Z')
    ]
    assert form.changes.data == ['a', 'b']

    form.apply_model()
    assert form.changes.data == ['a', 'b', 'c']

    form.update_model()
    assert form.model.apply.called


def test_user_group_form(session: Session) -> None:
    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')
    user_c = users.add(username='c@example.org', password='c', role='member')
    user_a.logout_all_sessions = MagicMock()  # type: ignore[method-assign]
    user_b.logout_all_sessions = MagicMock()  # type: ignore[method-assign]
    user_c.logout_all_sessions = MagicMock()  # type: ignore[method-assign]

    agencies = ExtendedAgencyCollection(session)
    agency_a = agencies.add_root(title="a")
    agency_a_1 = agencies.add(title="a.1", parent=agency_a)
    agency_b = agencies.add_root(title="b")

    request = DummyRequest(session)
    form = UserGroupForm()
    form.request = request
    form.on_request()

    # choices
    assert sorted([x[1] for x in form.users.choices]) == [
        'a@example.org', 'b@example.org', 'c@example.org',
    ]
    assert sorted([x[1] for x in form.agencies.choices]) == ['a', 'a.1', 'b']

    # apply / update
    groups = UserGroupCollection(session)
    group = groups.add(name='A')

    form.apply_model(group)
    assert form.name.data == 'A'
    assert form.users.data == []
    assert form.agencies.data == []
    assert form.immediate_notification.data == 'no'

    form.name.data = 'A/B'
    form.users.data = [str(user_a.id), str(user_b.id)]
    form.agencies.data = [str(agency_a.id), str(agency_b.id)]
    form.immediate_notification.data = 'yes'
    form.update_model(group)
    assert group.users.count() == 2
    assert group.role_mappings.count() == 2
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is False
    assert isinstance(group.meta, dict)
    assert group.meta['immediate_notification'] == 'yes'

    form.apply_model(group)
    assert form.name.data == 'A/B'
    assert set(form.users.data) == {str(user_a.id), str(user_b.id)}
    assert set(form.agencies.data) == {str(agency_a.id), str(agency_b.id)}
    assert form.immediate_notification.data == 'yes'

    user_a.logout_all_sessions.reset_mock()
    user_b.logout_all_sessions.reset_mock()
    user_c.logout_all_sessions.reset_mock()

    form.name.data = 'A.1'
    form.users.data = [str(user_c.id)]
    form.agencies.data = [str(agency_a_1.id)]
    form.immediate_notification.data = 'no'
    form.update_model(group)
    assert group.users.one() == user_c
    assert group.role_mappings.one().content_id == str(agency_a_1.id)
    assert group.meta['immediate_notification'] == 'no'
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is True
