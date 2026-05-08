from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from lxml import etree
from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote
from onegov.election_day.screen_widgets import (
    CountedEntitiesWidget,
    IfCompletedWidget,
    IfNotCompletedWidget,
    LastResultChangeWidget,
    ModelProgressWidget,
    ModelTitleWidget,
    NumberOfCountedEntitiesWidget,
    TotalEntitiesWidget,
    VoteCounterProposalDistrictsMap,
    VoteCounterProposalEntitiesMap,
    VoteCounterProposalEntitiesTableWidget,
    VoteCounterProposalResultBarWidget,
    VoteCounterProposalTitleWidget,
    VoteCounterProposalTurnoutWidget,
    VoteProposalDistrictsMap,
    VoteProposalEntitiesMap,
    VoteProposalEntitiesTableWidget,
    VoteProposalResultBarWidget,
    VoteProposalTurnoutWidget,
    VoteTieBreakerDistrictsMap,
    VoteTieBreakerEntitiesMap,
    VoteTieBreakerEntitiesTableWidget,
    VoteTieBreakerResultBarWidget,
    VoteTieBreakerTitleWidget,
    VoteTieBreakerTurnoutWidget
)
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.widgets import Widget
    from ..conftest import ImportTestDatasets, TestApp


def test_vote_widgets(
    election_day_app_zg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    structure = """
        <model-title class="my-class-1"/>
        <model-progress class="my-class-2"/>
        <counted-entities class="my-class-3"/>
        <vote-proposal-entities-table class="my-class-4"/>
        <vote-proposal-result-bar class="my-class-5"/>
        <vote-proposal-entities-map class="my-class-6"/>
        <vote-proposal-districts-map class="my-class-7"/>
        <number-of-counted-entities class="my-class-8"/>
        <total-entities class="my-class-9"/>
        <last-result-change class="my-class-a"/>
        <if-completed>is-completed</if-completed>
        <if-not-completed>is-not-completed</if-not-completed>
    """
    widgets: list[Widget] = [
        CountedEntitiesWidget(),
        IfCompletedWidget(),
        IfNotCompletedWidget(),
        LastResultChangeWidget(),
        ModelProgressWidget(),
        ModelTitleWidget(),
        NumberOfCountedEntitiesWidget(),
        TotalEntitiesWidget(),
        VoteProposalDistrictsMap(),
        VoteProposalEntitiesMap(),
        VoteProposalEntitiesTableWidget(),
        VoteProposalResultBarWidget(),
    ]

    # Empty
    session = election_day_app_zg.session()
    session.add(
        Vote(title='Vote', domain='canton', date=date(2015, 6, 18))
    )
    session.flush()
    model = session.query(Vote).one()
    request: Any = DummyRequest(app=election_day_app_zg, session=session)
    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    data['proposal_results'] = [x.name for x in data['proposal_results']]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': [],
        'embed': False,
        'entities': '',
        'request': request
    }
    assert '>Vote</span>' in result
    assert 'Not yet counted' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        results = import_test_datasets(
            'internal',
            'vote',
            'zg',
            'federation',
            date_=date(2015, 10, 18),
            dataset_name='ndg-intermediate',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        assert not errors
        session.add(model)
        session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    data['proposal_results'] = [x.name for x in data['proposal_results']]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': [
            'Baar',
            'Cham',
            'Hünenberg',
            'Menzingen',
            'Neuheim',
            'Oberägeri',
            'Risch',
            'Steinhausen',
            'Unterägeri',
            'Walchwil',
            'Zug'
        ],
        'embed': False,
        'entities': 'Baar',
        'request': request
    }
    assert '>simple_internal_ndg-intermediate</span>' in result
    assert '1 of 11' in result
    assert '>Baar</span>' in result
    assert 'ballot-entities-table' in result
    assert 'data-text="4447"' in result
    assert 'Not yet counted' in result
    assert 'ballot-result-bar' in result
    assert '68.22%' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert '1' in result
    assert '11' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert '01.01.2022' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        results = import_test_datasets(
            'internal',
            'vote',
            'zg',
            'federation',
            date_=date(2015, 10, 18),
            dataset_name='ndg',
            app_session=session
        )
        assert len(results) == 1
        model, errors = next(iter(results.values()))
        assert not errors
        session.add(model)
        session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    data['proposal_results'] = [x.name for x in data['proposal_results']]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': [
            'Baar',
            'Cham',
            'Hünenberg',
            'Menzingen',
            'Neuheim',
            'Oberägeri',
            'Risch',
            'Steinhausen',
            'Unterägeri',
            'Walchwil',
            'Zug'
        ],
        'embed': False,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'request': request
    }
    assert '>simple_internal_ndg</span>' in result
    assert '11 of 11' in result
    assert (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    ) in result
    assert 'ballot-entities-table' in result
    assert 'data-text="4447"' in result
    assert 'Not yet counted' not in result
    assert 'ballot-result-bar' in result
    assert '69.26%' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert '11' in result
    assert '11' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert '02.01.2022' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result


def test_complex_vote_widgets(
    election_day_app_zg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    structure = """
        <model-title class="my-class-1"/>
        <model-progress class="my-class-2"/>
        <counted-entities class="my-class-3"/>
        <vote-proposal-entities-table class="my-class-4"/>
        <vote-proposal-result-bar class="my-class-5"/>
        <vote-proposal-entities-map class="my-class-5"/>
        <vote-proposal-districts-map class="my-class-6"/>
        <vote-counter-proposal-title class="my-class-7"/>
        <vote-counter-proposal-entities-table class="my-class-8"/>
        <vote-counter-proposal-result-bar class="my-class-9"/>
        <vote-counter-proposal-entities-map class="my-class-a"/>
        <vote-counter-proposal-districts-map class="my-class-b"/>
        <vote-tie-breaker-title class="my-class-c"/>
        <vote-tie-breaker-entities-table class="my-class-d"/>
        <vote-tie-breaker-result-bar class="my-class-e"/>
        <vote-tie-breaker-entities-map class="my-class-f"/>
        <vote-tie-breaker-districts-map class="my-class-g"/>
        <number-of-counted-entities class="my-class-h"/>
        <total-entities class="my-class-i"/>
        <vote-counter-proposal-turnout class="my-class-j"/>
        <vote-proposal-turnout class="my-class-k"/>
        <vote-tie-breaker-turnout class="my-class-l"/>
        <last-result-change class="my-class-m"/>
        <if-completed>is-completed</if-completed>
        <if-not-completed>is-not-completed</if-not-completed>
    """
    widgets: list[Widget] = [
        CountedEntitiesWidget(),
        IfCompletedWidget(),
        IfNotCompletedWidget(),
        LastResultChangeWidget(),
        ModelProgressWidget(),
        ModelTitleWidget(),
        NumberOfCountedEntitiesWidget(),
        TotalEntitiesWidget(),
        VoteCounterProposalDistrictsMap(),
        VoteCounterProposalEntitiesMap(),
        VoteCounterProposalEntitiesTableWidget(),
        VoteCounterProposalResultBarWidget(),
        VoteCounterProposalTitleWidget(),
        VoteCounterProposalTurnoutWidget(),
        VoteProposalDistrictsMap(),
        VoteProposalEntitiesMap(),
        VoteProposalEntitiesTableWidget(),
        VoteProposalResultBarWidget(),
        VoteProposalTurnoutWidget(),
        VoteTieBreakerDistrictsMap(),
        VoteTieBreakerEntitiesMap(),
        VoteTieBreakerEntitiesTableWidget(),
        VoteTieBreakerResultBarWidget(),
        VoteTieBreakerTitleWidget(),
        VoteTieBreakerTurnoutWidget(),
    ]

    # Empty
    session = election_day_app_zg.session()
    session.add(
        ComplexVote(title='Proposal', domain='canton', date=date(2015, 6, 18))
    )
    model = session.query(ComplexVote).one()
    model.counter_proposal.title = 'Counter Proposal'
    model.tie_breaker.title = 'Tie Breaker'
    request: Any = DummyRequest(app=election_day_app_zg, session=session)
    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    for ballot in ('proposal', 'counter_proposal', 'tie_breaker'):
        data[f'{ballot}_results'] = [x.name for x in data[f'{ballot}_results']]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': [],
        'counter_proposal': model.counter_proposal,
        'counter_proposal_results': [],
        'tie_breaker': model.tie_breaker,
        'tie_breaker_results': [],
        'embed': False,
        'entities': '',
        'request': request
    }
    assert '>Proposal</span>' in result
    assert '>Counter Proposal</span>' in result
    assert '>Tie Breaker</span>' in result
    assert 'Not yet counted' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result
    assert 'my-class-l' in result
    assert 'my-class-m' in result

    # Add intermediate results
    with freeze_time('2022-01-01 12:00'):
        import_results = import_test_datasets(
            'internal',
            'vote',
            'zg',
            'federation',
            vote_type='complex',
            date_=date(2015, 10, 18),
            dataset_name='mundart-intermediate',
            app_session=session
        )
        assert len(import_results) == 1
        model, errors = next(iter(import_results.values()))
        assert not errors
        session.add(model)
        session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    for ballot in ('proposal', 'counter_proposal', 'tie_breaker'):
        data[f'{ballot}_results'] = [x.name for x in data[f'{ballot}_results']]
    results = [
        'Baar', 'Cham', 'Hünenberg', 'Menzingen', 'Neuheim', 'Oberägeri',
        'Risch', 'Steinhausen', 'Unterägeri', 'Walchwil', 'Zug'
    ]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': results,
        'counter_proposal': model.counter_proposal,
        'counter_proposal_results': results,
        'tie_breaker': model.tie_breaker,
        'tie_breaker_results': results,
        'embed': False,
        'entities': 'Baar',
        'request': request
    }
    assert '>complex_internal_mundart-intermediate</span>' in result
    assert '1 of 11' in result
    assert '>Baar</span>' in result
    assert 'ballot-entities-table' in result
    assert 'data-text="2483"' in result
    assert 'Not yet counted' in result
    assert 'ballot-result-bar' in result
    assert '41.40%' in result
    assert 'data-text="3547"' in result
    assert '60.55%' in result
    assert 'data-text="2254"' in result
    assert '38.37%' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert '1' in result
    assert '11' in result
    assert '42.21 %' in result
    assert '43.20 %' in result
    assert '42.32 %' in result
    assert 'is-completed' not in result
    assert 'is-not-completed' in result
    assert '01.01.2022' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result
    assert 'my-class-l' in result
    assert 'my-class-m' in result

    # Add final results
    with freeze_time('2022-01-02 12:00'):
        import_results = import_test_datasets(
            'internal',
            'vote',
            'zg',
            'federation',
            vote_type='complex',
            date_=date(2015, 10, 18),
            dataset_name='mundart',
            app_session=session
        )
        assert len(import_results) == 1
        model, errors = next(iter(import_results.values()))
        assert not errors
        session.add(model)
        session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)
    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))
    for ballot in ('proposal', 'counter_proposal', 'tie_breaker'):
        data[f'{ballot}_results'] = [x.name for x in data[f'{ballot}_results']]

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'proposal_results': results,
        'counter_proposal': model.counter_proposal,
        'counter_proposal_results': results,
        'tie_breaker': model.tie_breaker,
        'tie_breaker_results': results,
        'embed': False,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'request': request
    }
    assert '>complex_internal_mundart</span>' in result
    assert '11 of 11' in result
    assert (
        'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
        'Steinhausen, Unterägeri, Walchwil, Zug'
    ) in result
    assert 'ballot-entities-table' in result
    assert 'data-text="2483"' in result
    assert 'Not yet counted' not in result
    assert 'ballot-result-bar' in result
    assert '39.61%' in result
    assert 'data-text="3547"' in result
    assert '62.48%' in result
    assert 'data-text="2254"' in result
    assert '37.00%' in result
    assert 'data-dataurl="Ballot/by-entity"' in result
    assert 'data-dataurl="Ballot/by-district"' in result
    assert '11' in result
    assert '11' in result
    assert '44.93 %' in result
    assert '45.92 %' in result
    assert '44.17 %' in result
    assert 'is-completed' in result
    assert 'is-not-completed' not in result
    assert '02.01.2022' in result
    assert 'my-class-1' in result
    assert 'my-class-2' in result
    assert 'my-class-3' in result
    assert 'my-class-4' in result
    assert 'my-class-5' in result
    assert 'my-class-6' in result
    assert 'my-class-7' in result
    assert 'my-class-8' in result
    assert 'my-class-9' in result
    assert 'my-class-a' in result
    assert 'my-class-b' in result
    assert 'my-class-c' in result
    assert 'my-class-d' in result
    assert 'my-class-e' in result
    assert 'my-class-f' in result
    assert 'my-class-g' in result
    assert 'my-class-h' in result
    assert 'my-class-i' in result
    assert 'my-class-j' in result
    assert 'my-class-k' in result
    assert 'my-class-l' in result
    assert 'my-class-m' in result
