from datetime import date
from io import BytesIO
from onegov.election_day.formats import export_vote_ech_0252
from onegov.election_day.formats import import_vote_ech_0252
from tests.onegov.election_day.common import create_principal


def test_import_vote_ech_0252(session, import_test_datasets):

    vote, errors = import_test_datasets(
        'internal',
        'vote',
        'sg',
        'canton',
        date_=date(2017, 5, 21),
        vote_type='simple',
        dataset_name='energiegesetz-eng',
        has_expats=True
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert vote.proposal.results.count() == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52

    # Test a roundtrip
    principal = create_principal('sg')
    xml = export_vote_ech_0252(
        vote,
        canton_id=principal.canton_id,
        domain_of_influence=principal.get_ech_domain(vote)
    )
    errors = import_vote_ech_0252(
        vote,
        principal,
        BytesIO(xml.encode('utf-8')),
    )

    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 40.91
    assert vote.eligible_voters == 320996
    assert vote.progress == (78, 78)
    assert vote.proposal.results.count() == 78
    assert vote.proposal.yeas == 68346
    assert vote.proposal.nays == 62523
    assert vote.proposal.empty == 406
    assert vote.proposal.invalid == 52


def test_import_vote_ech_0252_complex(session, import_test_datasets):

    vote, errors = import_test_datasets(
        'internal',
        'vote',
        'bl',
        'canton',
        vote_type='complex',
        date_=date(2012, 11, 25),
        dataset_name='ja-zur-guten-schule-baselland',
        app_session=session
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert vote.ballots.count() == 3
    assert vote.proposal.eligible_voters == 186621
    assert vote.proposal.progress == (86, 86)
    assert vote.proposal.yeas == 18640
    assert vote.proposal.nays == 31692
    assert vote.proposal.empty == 1308
    assert vote.proposal.invalid == 620
    assert vote.counter_proposal.eligible_voters == 186621
    assert vote.counter_proposal.progress == (86, 86)
    assert vote.counter_proposal.yeas == 27737
    assert vote.counter_proposal.nays == 21384
    assert vote.counter_proposal.empty == 2519
    assert vote.counter_proposal.invalid == 620
    assert vote.tie_breaker.eligible_voters == 186621
    assert vote.tie_breaker.progress == (86, 86)
    assert vote.tie_breaker.yeas == 16059
    assert vote.tie_breaker.nays == 29584
    assert vote.tie_breaker.empty == 5997
    assert vote.tie_breaker.invalid == 620

    # Test a roundtrip
    principal = create_principal('bl')
    xml = export_vote_ech_0252(
        vote,
        canton_id=principal.canton_id,
        domain_of_influence=principal.get_ech_domain(vote)
    )
    errors = import_vote_ech_0252(
        vote,
        principal,
        BytesIO(xml.encode('utf-8')),
    )

    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert vote.ballots.count() == 3
    assert vote.proposal.eligible_voters == 186621
    assert vote.proposal.progress == (86, 86)
    assert vote.proposal.yeas == 18640
    assert vote.proposal.nays == 31692
    assert vote.proposal.empty == 1308
    assert vote.proposal.invalid == 620
    assert vote.counter_proposal.eligible_voters == 186621
    assert vote.counter_proposal.progress == (86, 86)
    assert vote.counter_proposal.yeas == 27737
    assert vote.counter_proposal.nays == 21384
    assert vote.counter_proposal.empty == 2519
    assert vote.counter_proposal.invalid == 620
    assert vote.tie_breaker.eligible_voters == 186621
    assert vote.tie_breaker.progress == (86, 86)
    assert vote.tie_breaker.yeas == 16059
    assert vote.tie_breaker.nays == 29584
    assert vote.tie_breaker.empty == 5997
    assert vote.tie_breaker.invalid == 620


# todo: add more tests
