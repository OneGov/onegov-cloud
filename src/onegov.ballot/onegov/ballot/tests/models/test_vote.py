from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.ballot import Vote


def test_vote(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()

    vote = session.query(Vote).one()

    assert vote.type == 'simple'
    assert vote.title == "Universal Healthcare"
    assert vote.domain == 'federation'
    assert vote.date == date(2015, 6, 14)
    assert vote.proposal
    assert vote.ballot('proposal')
    assert not vote.ballot('counter-proposal')
    assert not vote.ballot('tie-breaker')


def test_complex_vote(session):
    vote = ComplexVote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(vote)
    session.flush()

    vote = session.query(Vote).one()

    assert vote.type == 'complex'
    assert vote.title == "Universal Healthcare"
    assert vote.domain == 'federation'
    assert vote.date == date(2015, 6, 14)
    assert vote.proposal
    assert vote.counter_proposal
    assert vote.tie_breaker
    assert vote.ballot('proposal')
    assert vote.ballot('counter-proposal')
    assert vote.ballot('tie-breaker')


def test_ballot(session):
    vote = Vote(
        id='vote',
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )
    ballot = Ballot(
        type='proposal',
        title='Proposal',
        vote_id='vote'
    )
    ballot.results.append(
        BallotResult(
            district='ZG',
            name='Rotkreuz',
            counted=True,
            yeas=4982,
            nays=4452,
            empty=500,
            invalid=66,
            entity_id=1
        )
    )
    session.add(vote)
    session.add(ballot)
    session.flush()

    ballot = session.query(Ballot).one()

    assert ballot.type == 'proposal'
    assert ballot.title == "Proposal"
    assert ballot.vote.title == "Universal Healthcare"

    result = ballot.results.one()
    assert result.district == 'ZG'
    assert result.name == 'Rotkreuz'
    assert result.counted is True
    assert result.yeas == 4982
    assert result.nays == 4452
    assert result.empty == 500
    assert result.invalid == 66
    assert result.entity_id == 1


def test_vote_id_generation(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    assert vote.id == 'universal-healthcare'

    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    assert vote.id == 'universal-healthcare-1'

    vote = ComplexVote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    assert vote.id == 'universal-healthcare-2'


def test_ballot_answer_simple(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        type='proposal',
        vote_id=vote.id
    )

    ballot.results.extend([
        BallotResult(
            name='Ort A',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        ),
        BallotResult(
            name='Ort B',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    ])

    session.add(ballot)
    session.flush()

    # not all results are counted yet
    assert vote.answer is None

    for result in ballot.results:
        result.counted = True

    assert vote.answer == 'accepted'

    # if there are as many nays as yeas, we default to 'rejected' - in reality
    # this is very unlikely to happen
    for result in ballot.results:
        result.nays = 100

    assert vote.answer == 'rejected'


def test_ballot_nobody_voted_right(session):

    # if nobody casts a valid vote, the result is 100% no
    result = BallotResult(
        name='Ort A',
        counted=True,
        yeas=0,
        nays=0,
        invalid=100,
        empty=100
    )

    assert result.yeas_percentage == 0
    assert result.nays_percentage == 100.0

    # make sure this works in an aggregated fashion as well
    vote = Vote(
        title="Should we go voting?",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))

    session.flush()

    query = session.query(BallotResult)
    query = query.filter(BallotResult.yeas_percentage == 0.0)
    assert query.count() == 3


def test_ballot_answer_proposal_wins(session):
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))

    assert vote.answer == 'proposal'
    assert vote.yeas_percentage == 100.0
    assert vote.nays_percentage == 0


def test_ballot_answer_counter_proposal_wins(session):
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=0, nays=0, counted=True, entity_id=1))

    assert vote.answer == 'counter-proposal'
    assert vote.yeas_percentage == 100.0
    assert vote.nays_percentage == 0


def test_ballot_answer_counter_tie_breaker_decides(session):
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=70, nays=30, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=80, nays=20, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))

    assert vote.answer == 'proposal'
    assert vote.yeas_percentage == 70.0
    assert vote.nays_percentage == 30.0

    vote.tie_breaker.results[0].yeas = 0
    vote.tie_breaker.results[0].nays = 100

    assert vote.answer == 'counter-proposal'
    assert vote.yeas_percentage == 80.0
    assert vote.nays_percentage == 20.0


def test_ballot_answer_nobody_wins(session):
    vote = ComplexVote(
        title="Abstimmung mit Gegenentwurf",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))

    session.add(vote)
    session.flush()

    # if only the proposal is accepted, the proposal wins
    vote.proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.counter_proposal.results.append(
        BallotResult(
            name='x', yeas=0, nays=100, counted=True, entity_id=1))
    vote.tie_breaker.results.append(
        BallotResult(
            name='x', yeas=100, nays=0, counted=True, entity_id=1))

    assert vote.answer == 'rejected'


def test_vote_progress(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18),
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(name='1', counted=True, entity_id=1)
    )
    vote.proposal.results.append(
        BallotResult(name='2', counted=True, entity_id=1)
    )
    vote.proposal.results.append(
        BallotResult(name='3', counted=False, entity_id=1)
    )

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)


def test_vote_turnout(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(
            name='1',
            counted=True,
            eligible_voters=100,
            yeas=10,
            entity_id=1
        )
    )

    session.flush()

    assert vote.turnout == 10
    assert vote.proposal.turnout == 10


def test_vote_percentage_by_entity(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )

    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=1,
            counted=True, eligible_voters=100, yeas=75, nays=25
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=1,
            counted=True, eligible_voters=100, yeas=25, nays=75
        )
    )

    session.flush()

    assert vote.proposal.percentage_by_entity() == {
        1: {'counted': True, 'yeas_percentage': 50.0, 'nays_percentage': 50.0}
    }


def test_ballot_results_aggregation(session):
    vote = Vote(
        title="Universal Healthcare",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(vote)
    session.flush()

    ballot = Ballot(
        type='proposal',
        vote_id=vote.id
    )

    ballot.results.extend([
        BallotResult(
            district='ZG',
            name='Rotkreuz',
            counted=True,
            yeas=507,
            nays=69,
            empty=14,
            invalid=5,
            entity_id=1,
        ),
        BallotResult(
            district='ZG',
            name='Menzingen',
            counted=True,
            yeas=309,
            nays=28,
            empty=5,
            invalid=0,
            entity_id=1,
        )
    ])

    session.add(ballot)
    session.flush()

    assert ballot.yeas == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    assert int(session.query(Vote.yeas).one()[0]) == 309 + 507
    assert int(session.query(Vote.nays).one()[0]) == 69 + 28
    assert int(session.query(Vote.empty).one()[0]) == 14 + 5
    assert int(session.query(Vote.invalid).one()[0]) == 5 + 0

    session.query(Ballot.yeas).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (True, )
    session.query(Ballot.counted).first() == (True, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yeas_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62

    ballot = session.query(Ballot).one()
    ballot.results.append(
        BallotResult(
            district='ZG',
            name='Baar',
            counted=False,
            entity_id=1,
        ),
    )
    session.flush()

    assert ballot.yeas == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is None
    assert ballot.counted is False
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    session.query(Ballot.yeas).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (None, )
    session.query(Ballot.counted).first() == (False, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yeas_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62

    # mark as counted, but don't change any results from 0
    ballot.results.filter_by(name='Baar').one().counted = True
    session.flush()

    assert ballot.yeas == 309 + 507
    assert ballot.nays == 69 + 28
    assert ballot.empty == 14 + 5
    assert ballot.invalid == 5 + 0
    assert ballot.cast_ballots == 309 + 507 + 69 + 28 + 14 + 5 + 5 + 0
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    session.query(Ballot.yeas).first() == (309 + 507, )
    session.query(Ballot.nays).first() == (69 + 28, )
    session.query(Ballot.empty).first() == (14 + 5, )
    session.query(Ballot.invalid).first() == (5 + 0, )
    session.query(Ballot.accepted).first() == (True, )
    session.query(Ballot.counted).first() == (True, )
    session.query(Ballot.cast_ballots).first() == (
        309 + 507 + 69 + 28 + 14 + 5 + 5 + 0, )
    round(session.query(Ballot.yeas_percentage).first()[0], 2) == 89.38
    round(session.query(Ballot.nays_percentage).first()[0], 2) == 10.62


def test_vote_last_change(session):
    # Add vote
    with freeze_time("2014-01-01"):
        vote = Vote(
            title="Abstimmung",
            domain='federation',
            date=date(2015, 6, 18)
        )
        vote.ballots.append(Ballot(type='proposal'))
        session.add(vote)
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-01')
    assert vote.last_result_change is None

    # Add results
    with freeze_time("2014-01-02"):
        vote.proposal.results.append(
            BallotResult(
                name='x', yeas=100, nays=0, counted=True, entity_id=1
            )
        )
        vote.proposal.results.append(
            BallotResult(
                name='y', yeas=0, nays=100, counted=True, entity_id=1
            )
        )
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-02')
    assert vote.last_result_change.isoformat().startswith('2014-01-02')

    # Add another result
    with freeze_time("2014-01-03"):
        vote.proposal.results.append(
            BallotResult(
                name='z', yeas=100, nays=0, counted=True, entity_id=1
            )
        )
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-03')
    assert vote.last_result_change.isoformat().startswith('2014-01-03')

    # Change a result
    with freeze_time("2014-01-04"):
        vote.proposal.results[0].name = 'q'
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-04')
    assert vote.last_result_change.isoformat().startswith('2014-01-04')

    # Change a ballot
    with freeze_time("2014-01-05"):
        vote.proposal.title_translations = {'en': 'Proposal', 'de': 'Vorlage'}
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-05')
    assert vote.last_result_change.isoformat().startswith('2014-01-04')

    # Change the vote
    with freeze_time("2014-01-06"):
        vote.domain = 'canton'
        session.flush()

    assert vote.last_modified.isoformat().startswith('2014-01-06')
    assert vote.last_result_change.isoformat().startswith('2014-01-04')


def test_vote_export(session):
    vote = ComplexVote(
        title="Abstimmung",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.title_translations['it_CH'] = 'Votazione'

    session.add(vote)
    session.flush()

    assert vote.export() == []

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(
        Ballot(
            type='counter-proposal',
            title_translations={
                'de_CH': 'Gegenvorschlag',
                'it_CH': 'Controprogetto'
            }
        )
    )
    vote.ballots.append(
        Ballot(
            type='tie-breaker',
            title_translations={
                'de_CH': 'Stichfrage',
                'it_CH': 'Spareggio'
            }
        )
    )

    vote.proposal.results.append(
        BallotResult(
            name='Foo Town',
            counted=True,
            yeas=90,
            nays=45,
            invalid=5,
            empty=10,
            eligible_voters=150,
            entity_id=1,
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='Bar Town',
            counted=False,
            entity_id=2,
        )
    )
    vote.counter_proposal.results.append(
        BallotResult(
            name='Foo Town',
            counted=False,
            entity_id=1,
        )
    )

    session.flush()

    assert vote.export() == [
        {
            'title_de_CH': "Abstimmung",
            'title_it_CH': "Votazione",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'type': "proposal",
            'counted': False,
            'district': "",
            'name': "Bar Town",
            'entity_id': 2,
            'yeas': 0,
            'nays': 0,
            'invalid': 0,
            'empty': 0,
            'eligible_voters': 0
        },
        {
            'title_de_CH': "Abstimmung",
            'title_it_CH': "Votazione",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'type': "proposal",
            'counted': True,
            'district': "",
            'name': "Foo Town",
            'entity_id': 1,
            'yeas': 90,
            'nays': 45,
            'invalid': 5,
            'empty': 10,
            'eligible_voters': 150,
        },
        {
            'title_de_CH': "Gegenvorschlag",
            'title_it_CH': "Controprogetto",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'type': "counter-proposal",
            'counted': False,
            'district': "",
            'name': "Foo Town",
            'entity_id': 1,
            'yeas': 0,
            'nays': 0,
            'invalid': 0,
            'empty': 0,
            'eligible_voters': 0
        }
    ]


def test_vote_meta_data(session):
    vote = Vote(
        title="Is this a test?",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert not vote.meta

    session.add(vote)
    session.flush()

    assert not vote.meta

    vote.meta['a'] = 1
    assert vote.meta['a'] == 1

    session.flush()
    vote.meta['b'] = 2
    assert vote.meta['a'] == 1
    assert vote.meta['b'] == 2


def test_vote_status(session):
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert vote.status is None
    assert vote.completed is False

    session.add(vote)
    session.flush()

    # Set status
    vote.status = 'unknown'
    session.flush()
    assert vote.status == 'unknown'

    vote.status = 'interim'
    session.flush()
    assert vote.status == 'interim'

    vote.status = 'final'
    session.flush()
    assert vote.status == 'final'

    vote.status = None
    session.flush()
    assert vote.status is None

    # Test completed calcuation
    # ... empty vote
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    vote.ballots.append(Ballot(type='proposal'))
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... vote with some results
    vote.proposal.results.append(
        BallotResult(
            name='A',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='B',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... vote with all results
    session.query(BallotResult).filter_by(name='B').one().counted = True
    for status, completed in (
        (None, True), ('unknown', True), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... complex vote with some results
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))
    vote.type = 'complex'
    vote.__class__ = ComplexVote

    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    vote.counter_proposal.results.append(
        BallotResult(
            name='C',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    vote.counter_proposal.results.append(
        BallotResult(
            name='D',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    vote.tie_breaker.results.append(
        BallotResult(
            name='E',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    vote.tie_breaker.results.append(
        BallotResult(
            name='F',
            counted=False,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed

    # ... complex vote with all results
    session.query(BallotResult).filter_by(name='D').one().counted = True
    session.query(BallotResult).filter_by(name='F').one().counted = True
    for status, completed in (
        (None, True), ('unknown', True), ('interim', False), ('final', True)
    ):
        vote.status = status
        assert vote.completed == completed


def test_clear_ballot(session):
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    session.add(vote)
    session.flush()

    vote.ballots.append(Ballot(type='proposal'))
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            name='name',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )

    vote.proposal.clear_results()

    assert vote.proposal.results.first() is None


def test_clear_vote(session):
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    session.add(vote)
    session.flush()

    vote.ballots.append(Ballot(type='proposal'))
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            name='name',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )

    vote.clear_results()

    assert vote.status is None
    assert vote.proposal.results.first() is None


def test_vote_has_results(session):
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2015, 6, 14)
    )
    session.add(vote)
    session.flush()

    assert vote.has_results is False

    # Simple vote
    vote.ballots.append(Ballot(type='proposal'))
    vote.proposal.results.append(
        BallotResult(
            name='A',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    assert vote.has_results is True

    # Complex vote
    vote.ballots.append(Ballot(type='counter-proposal'))
    vote.ballots.append(Ballot(type='tie-breaker'))
    vote.type = 'complex'
    vote.__class__ = ComplexVote
    session.delete(vote.proposal.results.one())
    assert vote.has_results is False

    vote.counter_proposal.results.append(
        BallotResult(
            name='D',
            counted=True,
            yeas=100,
            nays=50,
            entity_id=1,
        )
    )
    assert vote.has_results is True
