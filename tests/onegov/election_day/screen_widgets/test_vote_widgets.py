from chameleon import PageTemplate
from datetime import date
from lxml import etree
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.screen_widgets import (
    ColumnWidget,
    CountedEntitiesWidget,
    ProgressWidget,
    RowWidget,
    TitleWidget,
    VoteCounterProposalEntitiesTableWidget,
    VoteCounterProposalResultBarWidget,
    VoteCounterProposalTitleWidget,
    VoteProposalEntitiesTableWidget,
    VoteProposalResultBarWidget,
    VoteTieBreakerEntitiesTableWidget,
    VoteTieBreakerResultBarWidget,
    VoteTieBreakerTitleWidget
)
from tests.onegov.election_day.common import DummyRequest


def test_vote_widgets(election_day_app, import_test_datasets):
    structure = """
        <row>
            <column span="1"><title /></column>
            <column span="1"><progress /></column>
            <column span="1"><counted-entities /></column>
            <column span="1"><vote-proposal-entities-table /></column>
            <column span="1"><vote-proposal-result-bar /></column>
        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        VoteProposalEntitiesTableWidget(),
        VoteProposalResultBarWidget(),
    ]

    # Empty
    session = election_day_app.session()
    session.add(
        Vote(title='Vote', domain='canton', date=date(2015, 6, 18))
    )
    session.flush()
    model = session.query(Vote).one()
    request = DummyRequest(app=election_day_app, session=session)
    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'entities': '',
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>Vote</span>' in result
    assert 'Not yet counted' in result

    # Add intermediate results
    model, errors = import_test_datasets(
        'internal',
        'vote',
        'zg',
        'federation',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='ndg-intermediate',
        app_session=session
    )
    assert not errors
    session.add(model)
    session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'entities': 'Baar',
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>simple_internal_ndg-intermediate</span>' in result
    assert '1 of 11' in result
    assert '<div>Baar</div>' in result
    assert 'ballot-entities-table' in result
    assert 'data-text="4447"' in result
    assert 'Not yet counted' in result
    assert 'ballot-result-bar' in result
    assert '68.22%' in result

    # Add final results
    model, errors = import_test_datasets(
        'internal',
        'vote',
        'zg',
        'federation',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='ndg',
        app_session=session
    )
    assert not errors
    session.add(model)
    session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>simple_internal_ndg</span>' in result
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


def test_complex_vote_widgets(election_day_app, import_test_datasets):
    structure = """
        <row>
            <column span="1"><title /></column>
            <column span="1"><progress /></column>
            <column span="1"><counted-entities /></column>
            <column span="1"><vote-proposal-entities-table /></column>
            <column span="1"><vote-proposal-result-bar /></column>
            <column span="1"><vote-counter-proposal-title /></column>
            <column span="1"><vote-counter-proposal-entities-table /></column>
            <column span="1"><vote-counter-proposal-result-bar /></column>
            <column span="1"><vote-tie-breaker-title /></column>
            <column span="1"><vote-tie-breaker-entities-table /></column>
            <column span="1"><vote-tie-breaker-result-bar /></column>
        </row>
    """
    widgets = [
        RowWidget(),
        ColumnWidget(),
        CountedEntitiesWidget(),
        ProgressWidget(),
        TitleWidget(),
        VoteCounterProposalEntitiesTableWidget(),
        VoteCounterProposalResultBarWidget(),
        VoteCounterProposalTitleWidget(),
        VoteProposalEntitiesTableWidget(),
        VoteProposalResultBarWidget(),
        VoteTieBreakerEntitiesTableWidget(),
        VoteTieBreakerResultBarWidget(),
        VoteTieBreakerTitleWidget()
    ]

    # Empty
    session = election_day_app.session()
    session.add(
        ComplexVote(title='Proposal', domain='canton', date=date(2015, 6, 18))
    )
    model = session.query(ComplexVote).one()
    model.counter_proposal.title = 'Counter Proposal'
    model.tie_breaker.title = 'Tie Breaker'
    request = DummyRequest(app=election_day_app, session=session)
    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'counter_proposal': model.counter_proposal,
        'tie_breaker': model.tie_breaker,
        'entities': '',
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>Proposal</span>' in result
    assert '<span>Counter Proposal</span>' in result
    assert '<span>Tie Breaker</span>' in result
    assert 'Not yet counted' in result

    # Add intermediate results
    model, errors = import_test_datasets(
        'internal',
        'vote',
        'zg',
        'federation',
        vote_type='complex',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='mundart-intermediate',
        app_session=session
    )
    assert not errors
    session.add(model)
    session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'counter_proposal': model.counter_proposal,
        'tie_breaker': model.tie_breaker,
        'entities': 'Baar',
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>complex_internal_mundart-intermediate</span>' in result
    assert '1 of 11' in result
    assert '<div>Baar</div>' in result
    assert 'ballot-entities-table' in result
    assert 'data-text="2483"' in result
    assert 'Not yet counted' in result
    assert 'ballot-result-bar' in result
    assert '41.40%' in result
    assert 'data-text="3547"' in result
    assert '60.55%' in result
    assert 'data-text="2254"' in result
    assert '38.37%' in result

    # Add final results
    model, errors = import_test_datasets(
        'internal',
        'vote',
        'zg',
        'federation',
        vote_type='complex',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='mundart',
        app_session=session
    )
    assert not errors
    session.add(model)
    session.flush()

    layout = VoteLayout(model, request)
    default = {'layout': layout, 'request': request}
    data = inject_variables(widgets, layout, structure, default, False)

    assert data == {
        'layout': layout,
        'model': model,
        'proposal': model.proposal,
        'counter_proposal': model.counter_proposal,
        'tie_breaker': model.tie_breaker,
        'entities': (
            'Baar, Cham, Hünenberg, Menzingen, Neuheim, Oberägeri, Risch, '
            'Steinhausen, Unterägeri, Walchwil, Zug'
        ),
        'request': request
    }

    result = transform_structure(widgets, structure)
    result = PageTemplate(result)(**data)
    etree.fromstring(result.encode('utf-8'))

    assert '<span>complex_internal_mundart</span>' in result
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
