from datetime import date
from onegov.ballot import Election
from onegov.election_day.forms import ElectionForm
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.tests import DummyRequest
from wtforms.validators import InputRequired


def test_election_form_domains():
    form = ElectionForm()
    assert ElectionForm().domain.choices is None

    form.set_domain(Canton(name='be', canton='be'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]

    form.set_domain(Municipality(name='bern', municipality='351'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal'),
        ('municipality', 'Communal')
    ]


def test_election_form_translations():
    form = ElectionForm()
    form.request = DummyRequest()
    form.request.default_locale = 'de_CH'
    form.on_request()
    assert isinstance(form.election_de.validators[0], InputRequired)
    assert form.election_fr.validators == []
    assert form.election_it.validators == []
    assert form.election_rm.validators == []

    form = ElectionForm()
    form.request = DummyRequest()
    form.request.default_locale = 'fr_CH'
    form.on_request()
    assert form.election_de.validators == []
    assert isinstance(form.election_fr.validators[0], InputRequired)
    assert form.election_it.validators == []
    assert form.election_rm.validators == []


def test_election_form_model(election_day_app):
    model = Election()
    model.title = 'Election (DE)'
    model.title_translations['de_CH'] = 'Election (DE)'
    model.title_translations['fr_CH'] = 'Election (FR)'
    model.title_translations['it_CH'] = 'Election (IT)'
    model.title_translations['rm_CH'] = 'Election (RM)'
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.type = 'proporz'
    model.number_of_mandates = 5
    model.related_link = 'http://u.rl'
    model.tacit = False

    form = ElectionForm()
    form.apply_model(model)

    assert form.election_de.data == 'Election (DE)'
    assert form.election_fr.data == 'Election (FR)'
    assert form.election_it.data == 'Election (IT)'
    assert form.election_rm.data == 'Election (RM)'
    assert form.date.data == date.today()
    assert form.domain.data == 'federation'
    assert form.shortcode.data == 'xy'
    assert form.election_type.data == 'proporz'
    assert form.mandates.data == 5
    assert form.related_link.data == 'http://u.rl'
    assert form.tacit.data is False

    form.election_de.data = 'An Election (DE)'
    form.election_fr.data = 'An Election (FR)'
    form.election_it.data = 'An Election (IT)'
    form.election_rm.data = 'An Election (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.election_type.data = 'majorz'
    form.mandates.data = 2
    form.absolute_majority.data = 10000
    form.related_link.data = 'http://ur.l'
    form.tacit.data = True

    form.update_model(model)

    assert model.title == 'An Election (DE)'
    assert model.title_translations['de_CH'] == 'An Election (DE)'
    assert model.title_translations['fr_CH'] == 'An Election (FR)'
    assert model.title_translations['it_CH'] == 'An Election (IT)'
    assert model.title_translations['rm_CH'] == 'An Election (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.type == 'majorz'
    assert model.number_of_mandates == 2
    assert model.absolute_majority == 10000
    assert model.related_link == 'http://ur.l'
    assert model.tacit is True
