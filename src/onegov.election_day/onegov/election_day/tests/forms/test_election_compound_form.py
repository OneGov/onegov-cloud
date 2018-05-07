from datetime import date
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.election_day.forms import ElectionCompoundForm
from onegov.election_day.tests.common import DummyPostData
from onegov.election_day.tests.common import DummyRequest
from wtforms.validators import InputRequired


def test_election_compound_form_populate(session):
    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)

    form.on_request()
    assert form.elections.choices == []

    session.add(
        ProporzElection(
            title='election-1',
            domain='region',
            shortcode='2',
            date=date(2001, 1, 1))
    )
    session.add(
        Election(
            title='election-2',
            domain='region',
            shortcode='1',
            date=date(2001, 1, 1))
    )
    session.add(
        Election(
            title='election-3',
            domain='region',
            date=date(2000, 1, 1))
    )
    session.add(
        Election(
            title='election-4',
            domain='federation',
            date=date(2001, 1, 1))
    )
    session.flush()

    form.on_request()
    assert form.elections.choices == [
        ('election-3', 'election-3 (majorz)'),
        ('election-2', 'election-2 (majorz)'),
        ('election-1', 'election-1 (proporz)')
    ]


def test_election_compound_form_validate(session):
    session.add(
        ProporzElection(
            title='election-1',
            domain='region',
            date=date(2001, 1, 1))
    )
    session.add(
        Election(
            title='election-2',
            domain='region',
            date=date(2001, 1, 1))
    )
    session.add(
        Election(
            title='election-3',
            domain='region',
            date=date(2001, 1, 1))
    )
    session.flush()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.on_request()
    form.process(DummyPostData({
        'election_de': 'Elections',
        'domain': 'canton',
        'date': '2012-01-01',
        'elections': ['election-1', 'election-2'],
    }))
    assert not form.validate()
    assert form.errors == {
        'elections': ['Select either majorz or proporz elections.']
    }

    form.process(DummyPostData({
        'election_de': 'Elections',
        'domain': 'canton',
        'date': '2012-01-01',
        'elections': ['election-1'],
    }))
    assert form.validate()

    form.process(DummyPostData({
        'election_de': 'Elections',
        'domain': 'canton',
        'date': '2012-01-01',
        'elections': ['election-2', 'election-3'],
    }))
    assert form.validate()


def test_election_compound_form_translations(session):
    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.on_request()
    assert isinstance(form.election_de.validators[0], InputRequired)
    assert form.election_fr.validators == []
    assert form.election_it.validators == []
    assert form.election_rm.validators == []

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'fr_CH'
    form.on_request()
    assert form.election_de.validators == []
    assert isinstance(form.election_fr.validators[0], InputRequired)
    assert form.election_it.validators == []
    assert form.election_rm.validators == []


def test_election_compound_form_model(session):
    date_ = date(2001, 1, 1)
    e1 = Election(domain='region', title='e', id='e-1', date=date_)
    e2 = Election(domain='region', title='e', id='e-2', date=date_)
    e3 = Election(domain='region', title='e', id='e-3', date=date_)
    session.add(e1)
    session.add(e2)
    session.add(e3)
    session.flush()

    model = ElectionCompound()
    model.title = 'Elections (DE)'
    model.title_translations['de_CH'] = 'Elections (DE)'
    model.title_translations['fr_CH'] = 'Elections (FR)'
    model.title_translations['it_CH'] = 'Elections (IT)'
    model.title_translations['rm_CH'] = 'Elections (RM)'
    model.date = date(2012, 1, 1)
    model.domain = 'canton'
    model.shortcode = 'xy'
    model.related_link = 'http://u.rl'
    model.elections = [e1, e2]
    session.add(model)

    form = ElectionCompoundForm()
    form.apply_model(model)

    assert form.election_de.data == 'Elections (DE)'
    assert form.election_fr.data == 'Elections (FR)'
    assert form.election_it.data == 'Elections (IT)'
    assert form.election_rm.data == 'Elections (RM)'
    assert form.date.data == date(2012, 1, 1)
    assert form.domain.data == 'canton'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'
    assert form.elections.data == ['e-1', 'e-2']

    form.election_de.data = 'Some Elections (DE)'
    form.election_fr.data = 'Some Elections (FR)'
    form.election_it.data = 'Some Elections (IT)'
    form.election_rm.data = 'Some Elections (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.elections.data = ['e-1', 'e-3', 'e-4']

    form.request = DummyRequest(session=session)
    form.on_request()
    form.update_model(model)

    assert model.title == 'Some Elections (DE)'
    assert model.title_translations['de_CH'] == 'Some Elections (DE)'
    assert model.title_translations['fr_CH'] == 'Some Elections (FR)'
    assert model.title_translations['it_CH'] == 'Some Elections (IT)'
    assert model.title_translations['rm_CH'] == 'Some Elections (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.related_link == 'http://ur.l'
    assert sorted([e.id for e in model.elections]) == ['e-1', 'e-3']
