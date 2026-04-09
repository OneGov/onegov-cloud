from __future__ import annotations

from datetime import date
from onegov.election_day.forms import ScreenForm
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Screen
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_screen_form_validate(election_day_app_zg: TestApp) -> None:
    session = election_day_app_zg.session()

    assert not ScreenForm().validate()

    form = ScreenForm(
        DummyPostData({
            'number': '2',
            'group': '',
            'duration': '',
            'description': 'My Screen',
            'type': 'majorz_election',
            'majorz_election': 'election',
            'structure': '<model-title />',
            'css': ''
        })
    )
    form.request = DummyRequest(app=election_day_app_zg, session=session)  # type: ignore[assignment]
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
            'structure': '<grid-row<model-title /></grid-row>',
            'css': ''
        })
    )
    form.request = DummyRequest(app=election_day_app_zg, session=session)  # type: ignore[assignment]
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
    form.request = DummyRequest(app=election_day_app_zg, session=session)  # type: ignore[assignment]
    form.majorz_election.choices = [('election', 'Election')]
    assert not form.validate()
    assert form.errors == {'structure': ["Invalid element '<fancy-stuff>'"]}


def test_screen_form_update_apply(session: Session) -> None:
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
    part = ElectionCompoundPart(compound, 'domain', 'segment')

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
    assert form.election_compound_part.data is False
    assert form.domain.data is None
    assert form.domain_segment.data is None
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
    form.election_compound_part.data = True
    form.domain.data = 'domain'
    form.domain_segment.data = 'segment'
    form.structure.data = '<h1><title /></h1>'
    form.css.data = ''
    form.update_model(model)
    session.flush()
    session.expire(model)
    assert model.number == 6
    assert model.group == 'A'
    assert model.duration == 10
    assert model.description == 'Screen'
    assert model.type == 'proporz_election'
    assert model.vote_id is None
    assert model.election_id == proporz.id
    assert model.election_compound_id is None
    assert model.election_compound_part is None
    assert model.domain is None
    assert model.domain_segment is None
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
    assert form.election_compound_part.data is False
    assert form.domain.data is None
    assert form.domain_segment.data is None
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
    session.flush()
    session.expire(model)
    # undo mypy narrowing
    model = model
    assert model.type == 'election_compound'
    assert model.vote_id is None
    assert model.election_id is None
    assert model.election_compound_id == compound.id
    assert model.election_compound_part is None
    assert model.domain is None
    assert model.domain_segment is None
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'election_compound'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == compound.id
    assert form.election_compound_part.data is False
    assert form.domain.data is None
    assert form.domain_segment.data is None

    # Election compound part
    form.type.data = 'election_compound'
    form.simple_vote.data = 'xxx'
    form.complex_vote.data = 'xxx'
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = compound.id
    form.election_compound_part.data = True
    form.domain.data = 'domain'
    form.domain_segment.data = 'segment'
    form.update_model(model)
    session.flush()
    session.expire(model)
    assert model.type == 'election_compound_part'
    assert model.vote_id is None
    assert model.election_id is None
    assert model.election_compound_id == compound.id
    assert model.election_compound_part == part
    assert model.domain == 'domain'
    assert model.domain_segment == 'segment'
    form = ScreenForm()
    form.apply_model(model)
    # undo mypy narrowing
    model = model
    assert form.type.data == 'election_compound'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == compound.id
    assert form.election_compound_part.data is True
    assert form.domain.data == 'domain'
    assert form.domain_segment.data == 'segment'

    # Simple vote
    form.type.data = 'simple_vote'
    form.simple_vote.data = simple.id
    form.complex_vote.data = 'xxx'
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = 'xxx'
    form.update_model(model)
    session.flush()
    session.expire(model)
    # undo mypy narrowing
    model = model
    assert model.type == 'simple_vote'
    assert model.vote_id == simple.id
    assert model.election_id is None
    assert model.election_compound_id is None
    assert model.election_compound_part is None
    assert model.domain is None
    assert model.domain_segment is None
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'simple_vote'
    assert form.simple_vote.data == simple.id
    assert form.complex_vote.data == ''
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == ''
    assert form.election_compound_part.data is False
    assert form.domain.data is None
    assert form.domain_segment.data is None

    # Complex vote
    form.type.data = 'complex_vote'
    form.simple_vote.data = 'xxx'
    form.complex_vote.data = complex.id
    form.majorz_election.data = 'xxx'
    form.proporz_election.data = 'xxx'
    form.election_compound.data = 'xxx'
    form.update_model(model)
    session.flush()
    session.expire(model)
    assert model.type == 'complex_vote'
    assert model.vote_id == complex.id
    assert model.election_id is None
    assert model.election_compound_id is None
    assert model.election_compound_part is None
    assert model.domain is None
    assert model.domain_segment is None
    form = ScreenForm()
    form.apply_model(model)
    assert form.type.data == 'complex_vote'
    assert form.simple_vote.data == ''
    assert form.complex_vote.data == complex.id
    assert form.majorz_election.data == ''
    assert form.proporz_election.data == ''
    assert form.election_compound.data == ''
    assert form.election_compound_part.data is False
    assert form.domain.data is None
    assert form.domain_segment.data is None


def test_screen_form_populate(election_day_app_zg: TestApp) -> None:
    session = election_day_app_zg.session()
    session.add(
        Vote(
            title='Simple 1',
            shortcode='m2',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        Vote(
            title='Simple 2',
            shortcode='m1',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        ComplexVote(
            title='Complex 1',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        Election(
            title='Majorz 1',
            shortcode='m2',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        Election(
            title='Majorz 2',
            shortcode='m1',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        ProporzElection(
            title='Proporz 1',
            domain='federation',
            date=date(2001, 1, 1)
        )
    )
    session.add(
        ElectionCompound(
            title='Elections 1',
            shortcode='e1',
            domain='canton',
            date=date(2001, 1, 1),
        )
    )
    session.add(
        ElectionCompound(
            title='Elections 2',
            shortcode='e2',
            domain='canton',
            date=date(2001, 1, 1),
        )
    )
    session.flush()

    form = ScreenForm()
    form.request = DummyRequest(app=election_day_app_zg, session=session)  # type: ignore[assignment]
    form.on_request()
    assert form.simple_vote.choices == [
        ('simple-2', 'Simple 2 [2001-01-01]'),
        ('simple-1', 'Simple 1 [2001-01-01]')
    ]
    assert form.complex_vote.choices == [
        ('complex-1', 'Complex 1 [2001-01-01]')
    ]
    assert form.majorz_election.choices == [
        ('majorz-2', 'Majorz 2 [2001-01-01]'),
        ('majorz-1', 'Majorz 1 [2001-01-01]')
    ]
    assert form.proporz_election.choices == [
        ('proporz-1', 'Proporz 1 [2001-01-01]')
    ]
    assert form.election_compound.choices == [
        ('elections-1', 'Elections 1 [2001-01-01]'),
        ('elections-2', 'Elections 2 [2001-01-01]')
    ]
    assert form.tags_simple_vote.text == (
        '<counted-entities class=""/>\n'
        '<grid-column span="" class=""></grid-column>\n'
        '<grid-row class=""></grid-row>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<if-completed></if-completed>\n'
        '<if-not-completed></if-not-completed>\n'
        '<last-result-change class=""/>\n'
        '<model-progress class=""/>\n'
        '<model-title class=""/>\n'
        '<number-of-counted-entities class=""/>\n'
        '<p class=""></p>\n'
        '<principal-logo class=""/>\n'
        '<qr-code class="" url="https://"/>\n'
        '<total-entities class=""/>\n'
        '<vote-proposal-districts-map class=""/>\n'
        '<vote-proposal-entities-map class=""/>\n'
        '<vote-proposal-entities-table class=""/>\n'
        '<vote-proposal-result-bar class=""/>\n'
        '<vote-proposal-turnout class=""/>'
    )
    assert form.tags_complex_vote.text == (
        '<counted-entities class=""/>\n'
        '<grid-column span="" class=""></grid-column>\n'
        '<grid-row class=""></grid-row>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<if-completed></if-completed>\n'
        '<if-not-completed></if-not-completed>\n'
        '<last-result-change class=""/>\n'
        '<model-progress class=""/>\n'
        '<model-title class=""/>\n'
        '<number-of-counted-entities class=""/>\n'
        '<p class=""></p>\n'
        '<principal-logo class=""/>\n'
        '<qr-code class="" url="https://"/>\n'
        '<total-entities class=""/>\n'
        '<vote-counter-proposal-districts-map class=""/>\n'
        '<vote-counter-proposal-entities-map class=""/>\n'
        '<vote-counter-proposal-entities-table class=""/>\n'
        '<vote-counter-proposal-result-bar class=""/>\n'
        '<vote-counter-proposal-title class=""/>\n'
        '<vote-counter-proposal-turnout class=""/>\n'
        '<vote-proposal-districts-map class=""/>\n'
        '<vote-proposal-entities-map class=""/>\n'
        '<vote-proposal-entities-table class=""/>\n'
        '<vote-proposal-result-bar class=""/>\n'
        '<vote-proposal-turnout class=""/>\n'
        '<vote-tie-breaker-districts-map class=""/>\n'
        '<vote-tie-breaker-entities-map class=""/>\n'
        '<vote-tie-breaker-entities-table class=""/>\n'
        '<vote-tie-breaker-result-bar class=""/>\n'
        '<vote-tie-breaker-title class=""/>\n'
        '<vote-tie-breaker-turnout class=""/>'
    )
    assert form.tags_majorz_election.text == (
        '<absolute-majority class=""/>\n'
        '<allocated-mandates class=""/>\n'
        '<counted-entities class=""/>\n'
        '<election-candidates-by-entity-table class=""/>\n'
        '<election-candidates-chart limit="" lists="," sort-by-lists=""'
        ' elected="" class=""/>\n'
        '<election-candidates-table class="" lists=","/>\n'
        '<election-turnout class=""/>\n'
        '<grid-column span="" class=""></grid-column>\n'
        '<grid-row class=""></grid-row>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<if-absolute-majority></if-absolute-majority>\n'
        '<if-completed></if-completed>\n'
        '<if-not-completed></if-not-completed>\n'
        '<if-relative-majority></if-relative-majority>\n'
        '<last-result-change class=""/>\n'
        '<mandates class=""/>\n'
        '<model-progress class=""/>\n'
        '<model-title class=""/>\n'
        '<number-of-counted-entities class=""/>\n'
        '<number-of-mandates class=""/>\n'
        '<p class=""></p>\n'
        '<principal-logo class=""/>\n'
        '<qr-code class="" url="https://"/>\n'
        '<total-entities class=""/>'
    )
    assert form.tags_proporz_election.text == (
        '<allocated-mandates class=""/>\n'
        '<counted-entities class=""/>\n'
        '<election-candidates-chart limit="" lists="," sort-by-lists=""'
        ' elected="" class=""/>\n'
        '<election-candidates-table class="" lists=","/>\n'
        '<election-lists-chart limit="" names="," sort-by-names=""'
        ' class=""/>\n'
        '<election-lists-table class="" names=","/>\n'
        '<election-party-strengths-chart horizontal="false" class=""/>\n'
        '<election-party-strengths-table year="" class=""/>\n'
        '<election-turnout class=""/>\n'
        '<grid-column span="" class=""></grid-column>\n'
        '<grid-row class=""></grid-row>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<if-completed></if-completed>\n'
        '<if-not-completed></if-not-completed>\n'
        '<last-result-change class=""/>\n'
        '<mandates class=""/>\n'
        '<model-progress class=""/>\n'
        '<model-title class=""/>\n'
        '<number-of-counted-entities class=""/>\n'
        '<number-of-mandates class=""/>\n'
        '<p class=""></p>\n'
        '<principal-logo class=""/>\n'
        '<qr-code class="" url="https://"/>\n'
        '<total-entities class=""/>'
    )
    assert form.tags_election_compound.text == (
        '<counted-entities class=""/>\n'
        '<election-compound-candidates-table class=""/>\n'
        '<election-compound-districts-map class=""/>\n'
        '<election-compound-districts-table class=""/>\n'
        '<election-compound-list-groups-chart class=""/>\n'
        '<election-compound-list-groups-table class="" />\n'
        '<election-compound-party-strengths-chart horizontal="false" '
        'class=""/>\n'
        '<election-compound-party-strengths-table year="" class=""/>\n'
        '<election-compound-seat-allocation-chart class=""/>\n'
        '<election-compound-seat-allocation-table class=""/>\n'
        '<election-compound-superregions-map class=""/>\n'
        '<election-compound-superregions-table class=""/>\n'
        '<grid-column span="" class=""></grid-column>\n'
        '<grid-row class=""></grid-row>\n'
        '<h1 class=""></h1>\n'
        '<h2 class=""></h2>\n'
        '<h3 class=""></h3>\n'
        '<hr class=""/>\n'
        '<if-completed></if-completed>\n'
        '<if-not-completed></if-not-completed>\n'
        '<last-result-change class=""/>\n'
        '<model-progress class=""/>\n'
        '<model-title class=""/>\n'
        '<number-of-counted-entities class=""/>\n'
        '<p class=""></p>\n'
        '<principal-logo class=""/>\n'
        '<qr-code class="" url="https://"/>\n'
        '<total-entities class=""/>'
    )
