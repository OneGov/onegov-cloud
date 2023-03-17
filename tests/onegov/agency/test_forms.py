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


class DummyApp:
    def __init__(self, session, principal):
        self._session = session

    def session(self):
        return self._session


class DummyRequest:
    def __init__(self, session, principal=None, private=False, secret=False,
                 permissions=None, current_user=None):
        self.app = DummyApp(session, principal)
        self.session = session
        self.private = private
        self.secret = secret
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'
        self.permissions = permissions or {}
        self.current_user = current_user
        self.client_addr = '1.1.1.1'

    def is_private(self, model):
        return self.private

    def is_secret(self, model):
        return self.secret

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate() if hasattr(text, 'interpolate') else text

    def has_permission(self, model, permission):
        permissions = self.permissions.get(model.__class__.__name__, [])
        return permission.__name__ in permissions


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def create_file(mimetype, filename, content):
    fs = FieldStorage()
    fs.file = TemporaryFile("wb+")
    fs.type = mimetype
    fs.filename = filename
    fs.file.write(content)
    fs.file.seek(0)
    return fs


def test_extended_agency_form(agency_app):
    # get useful data
    form = ExtendedAgencyForm(DummyPostData({
        'title': 'Springfield Hospital',
        'portrait': 'Springfield Hospital is hospital.',
        'coordinates': encode_map_value({'lat': 1, 'lon': 2, 'zoom': 12}),
        'export_fields': ['person.first_name', 'person.last_name'],
        'organigram': create_file('image/png', 'org.png', b'PNG')
    }))
    data = form.get_useful_data()
    assert list(data.keys()) == [
        'title', 'portrait', 'coordinates', 'export_fields', 'organigram_file'
    ]
    assert data['organigram_file'].read() == b'PNG'
    assert data['title'] == 'Springfield Hospital'
    assert data['portrait'] == 'Springfield Hospital is hospital.'
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
    assert model.organigram_file.read() == b'PNG'

    form = ExtendedAgencyForm()
    form.apply_model(model)
    assert form.title.data == 'Springfield Hospital'
    assert form.portrait.data == 'Springfield Hospital is hospital.'
    assert form.export_fields.data == ['person.first_name', 'person.last_name']
    assert form.export_fields.choices[:2] == [
        ('person.first_name', 'Person: First Name'),
        ('person.last_name', 'Person: Last Name')
    ]
    assert form.organigram.data['size']


def test_extended_agency_form_choices():
    models = {
        'membership': ExtendedAgencyMembership(),
        'person': ExtendedPerson(first_name="f", last_name="l")
    }

    form = ExtendedAgencyForm()
    for choice in form.export_fields.choices:
        model, attribute = choice[0].split('.')
        assert hasattr(models[model], attribute)


def test_move_agency_form(session):
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


def test_membership_form(session):
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


def test_membership_form_choices(session):
    people = ExtendedPersonCollection(session)
    people.add(first_name="Nick", last_name="Rivera")
    people.add(first_name="Nick", last_name="Rivera", phone="1234")
    people.add(first_name="Nick", last_name="Rivera", phone="5555", email="x")
    people.add(first_name="Nick", last_name="Rivera", phone_direct="4")
    people.add(first_name="Nick", last_name="Rivera", address="Street",
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


def test_agency_mutation_form():
    form = AgencyMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'title': 'Hospital Springfield'
    }))
    form.model = ExtendedAgency(title='Hopital Springfield')
    form.request = DummyRequest(None)
    form.on_request()

    assert set(form.proposal_fields.keys()) == {'title'}
    assert form.title.description == 'Hopital Springfield'
    assert form.proposed_changes == {'title': 'Hospital Springfield'}
    assert form.get_useful_data() == {
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'title': 'Hospital Springfield'
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
    form.request = DummyRequest(None)
    assert not form.validate()


def test_person_mutation_form():
    form = PersonMutationForm(DummyPostData({
        'submitter_email': 'info@hospital-springfield.org',
        'submitter_message': 'There is a typo in the name!',
        'first_name': 'nick',
        'last_name': 'Rivera',
        'academic_title': 'Dr.'
    }))
    form.model = ExtendedPerson(first_name="Nick", last_name="Riviera")
    form.request = DummyRequest(None)
    form.on_request()

    assert set(form.proposal_fields.keys()) == {
        'function', 'website', 'political_party', 'salutation', 'email',
        'notes', 'first_name', 'last_name', 'born', 'phone',
        'parliamentary_group', 'address', 'postal_code_city', 'profession',
        'phone_direct', 'academic_title'
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
        'address': None,
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
    form.request = DummyRequest(None)
    assert not form.validate()


def test_apply_muation_form():
    form = ApplyMutationForm(DummyPostData({'changes': ['a', 'b']}))
    form.request = DummyRequest(None)
    form.model = Bunch(
        labels={'a': 'A', 'c': 'C'},
        changes={'a': 'X', 'b': 'Y', 'c': 'Z'},
        apply=MagicMock()
    )
    form.on_request()
    assert form.changes.choices == (
        ('a', 'A: X'), ('b', 'b: Y'), ('c', 'C: Z')
    )
    assert form.changes.data == ['a', 'b']

    form.apply_model()
    assert form.changes.data == ['a', 'b', 'c']

    form.update_model()
    assert form.model.apply.called


def test_user_group_form(session):
    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')
    user_c = users.add(username='c@example.org', password='c', role='member')
    user_a.logout_all_sessions = MagicMock()
    user_b.logout_all_sessions = MagicMock()
    user_c.logout_all_sessions = MagicMock()

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
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is True
    assert group.meta['immediate_notification'] == 'no'
