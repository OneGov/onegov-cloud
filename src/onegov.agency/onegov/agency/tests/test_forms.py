from cgi import FieldStorage
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.forms import ExtendedAgencyForm
from onegov.agency.forms import MembershipForm
from onegov.agency.forms import MutationForm
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from tempfile import TemporaryFile


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session

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
        'export_fields': ['person.first_name', 'person.last_name'],
        'organigram': create_file('image/png', 'org.png', b'PNG')
    }))
    data = form.get_useful_data()
    assert list(data.keys()) == [
        'title', 'portrait', 'export_fields', 'organigram_file'
    ]
    assert data['organigram_file'].read() == b'PNG'
    assert data['title'] == 'Springfield Hospital'
    assert data['portrait'] == 'Springfield Hospital is hospital.'
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


def test_mutation_form():
    form = MutationForm(DummyPostData({
        'email': 'info@hospital-springfield.org',
        'message': "Nick Rivera's retired."
    }))
    assert form.get_useful_data() == {
        'email': 'info@hospital-springfield.org',
        'message': "Nick Rivera's retired."
    }
