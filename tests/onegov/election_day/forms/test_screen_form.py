from datetime import date
from onegov.ballot import ComplexVote
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.ballot import Vote
from onegov.election_day.forms import ScreenForm
from onegov.election_day.models import Screen
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest


def test_screen_form_validate(election_day_app):
    session = election_day_app.session()

    assert not ScreenForm().validate()

    form = ScreenForm(
        DummyPostData({
            'number': '2',
            'group': '',
            'duration': '',
            'description': 'My Screen',
            'type': 'majorz_election',
            'majorz_election': 'election',
            'structure': '<title />',
            'css': ''
        })
    )
    form.request = DummyRequest(app=election_day_app, session=session)
    form.majorz_election.choices = [('election', 'Election')]
    assert form.validate()

    form = ScreenForm(
        DummyPostData({
            'number': '2',
            'group': '',
            'duration': '',
            'description': 'My Screen',
            'type': 'majorz_election',
            'majorz_election': 'election',
            'structure': '<row<title /></row>',
            'css': ''
        })
    )
    form.request = DummyRequest(app=election_day_app, session=session)
    form.majorz_election.choices = [('election', 'Election')]
    assert not form.validate()
    assert form.errors == {'structure': ['error parsing attribute name']}

    form = ScreenForm(
        DummyPostData({
            'number': '2',
            'group': '',
            'duration': '',
            'description': 'My Screen',
            'type': 'majorz_election',
            'majorz_election': 'election',
            'structure': '<fancy-stuff />',
            'css': ''
        })
    )
    form.request = DummyRequest(app=election_day_app, session=session)
    form.majorz_election.choices = [('election', 'Election')]
    assert not form.validate()
    assert form.errors == {'structure': ["Invalid element '<fancy-stuff>'"]}


def test_screen_form_update_apply(session):
    simple = Vote(
        title='Simple',
        domain='federation',
        date=date(2015, 6, 14)
    )
    complex = ComplexVote(
        title='Complex',
        domain='federation',
        date=date(2015, 6, 14)
    )
    majorz = Election(
        title='Majorz',
        domain='federation',
        date=date(2015, 6, 14)
    )
    proporz = ProporzElection(
        title='Proporz',
        domain='federation',
        date=date(2015, 6, 14)
    )
    compound = ElectionCompound(
        title='Elections',
        domain='canton',
        date=date(2015, 6, 14),
    )
    session.add(simple)
    session.add(complex)
    session.add(majorz)
    session.add(proporz)
    session.add(compound)
    session.flush()

    # Create model
    model = Screen(
        number=5,
        group=None,
        duration=None,
        type='majorz_election',
        structure='<title />',
        election_id=majorz.id,
        description='My Screen',
        css='h1 { font-size: 20em; }'
    )
    session.add(model)
    session.flush()

    # Test apply
    form = ScreenForm()
    form.apply_model(model)
    assert form.number.data == 5
    assert form.group.data is None
    assert form.duration.data is None
    assert form.description.data == 'My Screen'
    assert form.type.data == 'majorz_election'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == majorz.id
    assert form.proporz_election.data == ''
    assert form.election_compound.data == ''
    assert form.structure.data == '<title />'
    assert form.css.data == 'h1 { font-size: 20em; }'

    # Test change all fields with update and apply
    form.number.data = 6
    form.group.data = 'A'
    form.duration.data = 10
    form.description.data = 'Screen'
    form.type.data = 'proporz_election'
    form.simple_vote.data = 'xxx'
    form.complex_vote.data = 'xxx'
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = proporz.id
    form.election_compound.data = 'xxx'
    form.structure.data = '<h1><title /></h1>'
    form.css.data = ''
    form.update_model(model)
    assert model.number == 6
    assert model.group == 'A'
    assert model.duration == 10
    assert model.description == 'Screen'
    assert model.type == 'proporz_election'
    assert model.vote_id is None
    assert model.election_id == proporz.id
    assert model.election_compound_id is None
    assert model.structure == '<h1><title /></h1>'
    assert model.css == ''
    form = ScreenForm()
    form.apply_model(model)
    assert form.number.data == 6
    assert model.group == 'A'
    assert model.duration == 10
    assert form.description.data == 'Screen'
    assert form.type.data == 'proporz_election'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == proporz.id
    assert form.election_compound.data == ''
    assert form.structure.data == '<h1><title /></h1>'
    assert form.css.data == ''

    # Election compound
    form.type.data = 'election_compound'
    form.simple_vote.data = 'xxx'
    form.complex_vote.data = 'xxx'
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = compound.id
    form.update_model(model)
    assert model.type == 'election_compound'
    assert model.vote_id is None
    assert model.election_id is None
    assert model.election_compound_id == compound.id
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'election_compound'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == compound.id

    # Simple vote
    form.type.data = 'simple_vote'
    form.simple_vote.data = simple.id
    form.complex_vote.data = 'xxx'
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = 'xxx'
    form.update_model(model)
    assert model.type == 'simple_vote'
    assert model.vote_id == simple.id
    assert model.election_id is None
    assert model.election_compound_id is None
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'simple_vote'
    assert form.simple_vote.data == simple.id
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == ''

    # Complex vote
    form.type.data = 'complex_vote'
    form.simple_vote.data = 'xxx'
    form.complex_vote.data = complex.id
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = 'xxx'
    form.update_model(model)
    assert model.type == 'complex_vote'
    assert model.vote_id == complex.id
    assert model.election_id is None
    assert model.election_compound_id is None
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'complex_vote'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == complex.id
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == ''


def test_screen_form_populate(election_day_app):
    session = election_day_app.session()
    session.add(
        Vote(
            title='Simple 1',
            shortcode='m2',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        Vote(
            title='Simple 2',
            shortcode='m1',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        ComplexVote(
            title='Complex 1',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        Election(
            title='Majorz 1',
            shortcode='m2',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        Election(
            title='Majorz 2',
            shortcode='m1',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        ProporzElection(
            title='Proporz 1',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        ElectionCompound(
            title='Elections 1',
            shortcode='e1',
            domain='canton',
            date=date(2015, 6, 14),
        )
    )
    session.add(
        ElectionCompound(
            title='Elections 2',
            shortcode='e2',
            domain='canton',
            date=date(2015, 6, 14),
        )
    )
    session.flush()

    form = ScreenForm()
    form.request = DummyRequest(app=election_day_app, session=session)
    form.on_request()
    assert form.simple_vote.choices == [
        ('simple-2', 'Simple 2'), ('simple-1', 'Simple 1')
    ]
    assert form.complex_vote.choices == [
        ('complex-1', 'Complex 1')
    ]
    assert form.majorz_election.choices == [
        ('majorz-2', 'Majorz 2'), ('majorz-1', 'Majorz 1')
    ]
    assert form.proporz_election.choices == [
        ('proporz-1', 'Proporz 1')
    ]
    assert form.election_compound.choices == [
        ('elections-1', 'Elections 1'), ('elections-2', 'Elections 2')
    ]

    assert form.tags_simple_vote.text == (
        '<column span="" class=""></column>\n'
        '<counted-entities class=""/>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<logo class=""/>\n'
        '<progress class=""/>\n'
        '<row class=""></row>\n'
        '<text class=""></text>\n'
        '<title class=""/>\n'
        '<vote-proposal-districts-map class=""/>\n'
        '<vote-proposal-entities-map class=""/>\n'
        '<vote-proposal-entities-table class=""/>\n'
        '<vote-proposal-result-bar class=""/>'
    )
    assert form.tags_complex_vote.text == (
        '<column span="" class=""></column>\n'
        '<counted-entities class=""/>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<logo class=""/>\n'
        '<progress class=""/>\n'
        '<row class=""></row>\n'
        '<text class=""></text>\n'
        '<title class=""/>\n'
        '<vote-counter-proposal-districts-map class=""/>\n'
        '<vote-counter-proposal-entities-map class=""/>\n'
        '<vote-counter-proposal-entities-table class=""/>\n'
        '<vote-counter-proposal-result-bar class=""/>\n'
        '<vote-counter-proposal-title class=""/>\n'
        '<vote-proposal-districts-map class=""/>\n'
        '<vote-proposal-entities-map class=""/>\n'
        '<vote-proposal-entities-table class=""/>\n'
        '<vote-proposal-result-bar class=""/>\n'
        '<vote-tie-breaker-districts-map class=""/>\n'
        '<vote-tie-breaker-entities-map class=""/>\n'
        '<vote-tie-breaker-entities-table class=""/>\n'
        '<vote-tie-breaker-result-bar class=""/>\n'
        '<vote-tie-breaker-title class=""/>'
    )
    assert form.tags_majorz_election.text == (
        '<column span="" class=""></column>\n'
        '<counted-entities class=""/>\n'
        '<election-candidates-chart limit="" class=""/>\n'
        '<election-candidates-table class=""/>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<logo class=""/>\n'
        '<progress class=""/>\n'
        '<row class=""></row>\n'
        '<text class=""></text>\n'
        '<title class=""/>'
    )
    assert form.tags_proporz_election.text == (
        '<column span="" class=""></column>\n'
        '<counted-entities class=""/>\n'
        '<election-candidates-chart limit="" class=""/>\n'
        '<election-candidates-table class=""/>\n'
        '<election-lists-chart limit="" class=""/>\n'
        '<election-lists-table class=""/>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<logo class=""/>\n'
        '<progress class=""/>\n'
        '<row class=""></row>\n'
        '<text class=""></text>\n'
        '<title class=""/>'
    )
    assert form.tags_election_compound.text == (
        '<column span="" class=""></column>\n'
        '<counted-entities class=""/>\n'
        '<election-compound-candidates-table class=""/>\n'
        '<election-compound-districts-table class=""/>\n'
        '<election-compound-lists-chart limit="" class=""/>\n'
        '<election-compound-lists-table class=""/>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<logo class=""/>\n'
        '<progress class=""/>\n'
        '<row class=""></row>\n'
        '<text class=""></text>\n'
        '<title class=""/>'
    )
