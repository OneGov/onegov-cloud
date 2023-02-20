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
    def result(name, counted):
        return BallotResult(name=name, counted=counted, entity_id=1)

    # Simple vote
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18),
    )
    session.add(vote)
    session.flush()

    assert vote.progress == (0, 0)
    assert vote.proposal.progress == (0, 0)
    assert vote.counted_entities == []

    vote.proposal.results.append(result('A', True))
    vote.proposal.results.append(result('B', True))
    vote.proposal.results.append(result('C', False))

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)
    assert vote.counted_entities == ['A', 'B']

    # Complex vote
    vote = ComplexVote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18),
    )
    session.add(vote)
    session.flush()

    assert vote.progress == (0, 0)
    assert vote.proposal.progress == (0, 0)
    assert vote.counter_proposal.progress == (0, 0)
    assert vote.tie_breaker.progress == (0, 0)
    assert vote.counted_entities == []

    vote.proposal.results.append(result('A', True))
    vote.proposal.results.append(result('B', True))
    vote.proposal.results.append(result('C', False))
    vote.counter_proposal.results.append(result('A', True))
    vote.counter_proposal.results.append(result('B', True))
    vote.counter_proposal.results.append(result('C', False))
    vote.tie_breaker.results.append(result('A', True))
    vote.tie_breaker.results.append(result('B', True))
    vote.tie_breaker.results.append(result('C', False))

    assert vote.progress == (2, 3)
    assert vote.proposal.progress == (2, 3)
    assert vote.counter_proposal.progress == (2, 3)
    assert vote.tie_breaker.progress == (2, 3)
    assert vote.counted_entities == ['A', 'B']


def test_vote_results_by_district(session):
    vote = Vote(
        title="Abstimmung",
        domain='federation',
        date=date(2015, 6, 18)
    )
    vote.ballots.append(Ballot(type='proposal'))
    session.add(vote)
    session.flush()
    assert vote.proposal.results_by_district.all() == []

    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=1,
            counted=True, eligible_voters=100,
            yeas=75, nays=25
        )
    )
    session.flush()
    assert [list(r) for r in vote.proposal.results_by_district] == [
        [None, True, True, 75, 25, 75.0, 25.0, 0, 0, 100, [1]]
    ]

    vote.proposal.results.append(
        BallotResult(
            name='2', entity_id=2,
            counted=False, eligible_voters=100,
            yeas=25, nays=75
        )
    )
    session.flush()
    assert [list(r) for r in vote.proposal.results_by_district] == [
        [None, False, None, 100, 100, 50.0, 50.0, 0, 0, 200, [1, 2]]
    ]

    vote.proposal.results.append(
        BallotResult(
            name='1', entity_id=3, district='a',
            counted=True, eligible_voters=100,
            empty=1, invalid=2, yeas=10, nays=30
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='2', entity_id=4, district='a',
            counted=True, eligible_voters=200,
            empty=3, invalid=4, yeas=50, nays=10
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='3', entity_id=5, district='b',
            counted=True, eligible_voters=300,
            empty=5, invalid=6, yeas=30, nays=10
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='4', entity_id=6, district='b',
            counted=True, eligible_voters=400,
            empty=7, invalid=8, yeas=10, nays=50
        )
    )
    assert [list(r) for r in vote.proposal.results_by_district] == [
        ['a', True, True, 60, 40, 60.0, 40.0, 4, 6, 300, [3, 4]],
        ['b', True, False, 40, 60, 40.0, 60.0, 12, 14, 700, [5, 6]],
        [None, False, None, 100, 100, 50.0, 50.0, 0, 0, 200, [1, 2]]
    ]


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
            eligible_voters=2877,
            expats=17,
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
            eligible_voters=1255,
            expats=1,
            yeas=309,
            nays=28,
            empty=5,
            invalid=0,
            entity_id=1,
        )
    ])

    session.add(ballot)
    session.flush()

    assert ballot.yeas == 816
    assert ballot.nays == 97
    assert ballot.empty == 19
    assert ballot.invalid == 5
    assert ballot.eligible_voters == 4132
    assert ballot.expats == 18
    assert ballot.cast_ballots == 937
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4132
    assert session.query(Ballot.expats).scalar() == 18
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert session.query(Ballot.accepted).scalar() is True
    assert session.query(Ballot.counted).scalar() is True
    # assert session.query(Ballot.yeas_percentage).scalar() == 89.38 OGC-533
    # assert session.query(Ballot.nays_percentage).scalar() == 10.62 OGC-533

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4132
    assert vote.expats == 18
    assert vote.cast_ballots == 937
    assert vote.counted is True
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4132
    assert session.query(Vote.expats).scalar() == 18
    assert session.query(Vote.cast_ballots).scalar() == 937

    ballot = session.query(Ballot).one()
    ballot.results.append(
        BallotResult(
            district='ZG',
            name='Baar',
            counted=False,
            entity_id=1,
            eligible_voters=420,
            expats=10
        ),
    )
    session.flush()

    assert ballot.yeas == 816
    assert ballot.nays == 97
    assert ballot.empty == 19
    assert ballot.invalid == 5
    assert ballot.eligible_voters == 4552
    assert ballot.expats == 28
    assert ballot.cast_ballots == 937
    assert ballot.accepted is None
    assert ballot.counted is False
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4552
    # OGC-533
    assert session.query(Ballot.expats).scalar() == 28
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert session.query(Ballot.accepted).scalar() is None
    assert session.query(Ballot.counted).scalar() is False
    # assert session.query(Ballot.yeas_percentage).scalar() == 89.38  # OGC-533
    # assert session.query(Ballot.nays_percentage).scalar() == 10.62  # OGC-533

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4552
    assert vote.expats == 28
    assert vote.cast_ballots == 937
    assert vote.counted is False
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4552
    # OGC-533
    assert session.query(Vote.expats).scalar() == 28
    assert session.query(Vote.cast_ballots).scalar() == 937

    # mark as counted, but don't change any results from 0
    ballot.results.filter_by(name='Baar').one().counted = True
    session.flush()

    assert ballot.yeas == 816
    assert ballot.nays == 97
    assert ballot.empty == 19
    assert ballot.invalid == 5
    assert ballot.eligible_voters == 4552
    assert ballot.expats == 28
    assert ballot.cast_ballots == 937
    assert ballot.accepted is True
    assert ballot.counted is True
    assert round(ballot.yeas_percentage, 2) == 89.38
    assert round(ballot.nays_percentage, 2) == 10.62

    assert session.query(Ballot.yeas).scalar() == 816
    assert session.query(Ballot.nays).scalar() == 97
    assert session.query(Ballot.empty).scalar() == 19
    assert session.query(Ballot.invalid).scalar() == 5
    assert session.query(Ballot.eligible_voters).scalar() == 4552
    assert session.query(Ballot.expats).scalar() == 28
    assert session.query(Ballot.cast_ballots).scalar() == 937
    assert session.query(Ballot.accepted).scalar() is True
    assert session.query(Ballot.counted).scalar() is True
    # assert session.query(Ballot.yeas_percentage).scalar() == 89.38  # OGC-533
    # assert session.query(Ballot.nays_percentage).scalar() == 10.62  # OGC-533

    assert vote.yeas == 816
    assert vote.nays == 97
    assert vote.empty == 19
    assert vote.invalid == 5
    assert vote.eligible_voters == 4552
    assert vote.expats == 28
    assert vote.cast_ballots == 937
    assert vote.counted is True
    assert round(vote.yeas_percentage, 2) == 89.38
    assert round(vote.nays_percentage, 2) == 10.62

    assert session.query(Vote.yeas).scalar() == 816
    assert session.query(Vote.nays).scalar() == 97
    assert session.query(Vote.empty).scalar() == 19
    assert session.query(Vote.invalid).scalar() == 5
    assert session.query(Vote.eligible_voters).scalar() == 4552
    assert session.query(Vote.expats).scalar() == 28
    assert session.query(Vote.cast_ballots).scalar() == 937


def test_vote_last_modified(session):
    # Add vote
    with freeze_time("2001-01-01"):
        vote = Vote(
            title="Abstimmung",
            domain='federation',
            date=date(2015, 6, 18)
        )
        assert vote.last_ballot_change is None
        assert vote.last_modified is None

        session.add(vote)
        session.flush()
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified.isoformat().startswith('2001')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2001')

    with freeze_time("2002-01-01"):
        vote.last_result_change = vote.timestamp()
        session.flush()
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified.isoformat().startswith('2002')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2002')

    with freeze_time("2003-01-01"):
        vote.domain = 'canton'
        session.flush()
        assert vote.last_ballot_change is None
        assert session.query(Vote.last_ballot_change).scalar() is None
        assert vote.last_modified.isoformat().startswith('2003')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2003')

    with freeze_time("2004-01-01"):
        vote.ballots.append(Ballot(type='proposal'))
        session.flush()
        assert vote.last_ballot_change.isoformat().startswith('2004')
        assert session.query(Vote.last_ballot_change).scalar()\
            .isoformat().startswith('2004')
        assert vote.last_modified.isoformat().startswith('2004')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2004')

    with freeze_time("2005-01-01"):
        vote.ballots.one().title = 'Proposal'
        session.flush()
        assert vote.last_ballot_change.isoformat().startswith('2005')
        assert session.query(Vote.last_ballot_change).scalar()\
            .isoformat().startswith('2005')
        assert vote.last_modified.isoformat().startswith('2005')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2005')

    with freeze_time("2006-01-01"):
        vote.ballots.append(Ballot(type='counter-proposal'))
        session.flush()
        assert vote.last_ballot_change.isoformat().startswith('2006')
        assert session.query(Vote.last_ballot_change).scalar()\
            .isoformat().startswith('2006')
        assert vote.last_modified.isoformat().startswith('2006')
        assert session.query(Vote.last_modified).scalar()\
            .isoformat().startswith('2006')
    return


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

    assert vote.export(['de_CH']) == []

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
            expats=30,
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

    assert vote.export(['de_CH', 'fr_CH', 'it_CH']) == [
        {
            'title_de_CH': "Abstimmung",
            'title_fr_CH': "",
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
            'eligible_voters': 0,
            'expats': ''
        },
        {
            'title_de_CH': "Abstimmung",
            'title_fr_CH': "",
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
            'expats': 30,
        },
        {
            'title_de_CH': "Gegenvorschlag",
            'title_fr_CH': "",
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
            'eligible_voters': 0,
            'expats': ''
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
    assert session.query(BallotResult).first() is None


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
    vote.last_result_change = vote.timestamp()

    vote.clear_results()

    assert vote.last_result_change is None
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


def test_vote_rename(session):
    vote = Vote(
        title='Vote',
        id='vorte',
        domain='canton',
        date=date(2017, 1, 1)
    )
    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(Ballot(type='counter-proposal'))
    session.add(vote)
    session.flush()

    assert session.query(Ballot.vote_id.distinct()).one()[0] == 'vorte'

    vote.id = 'vote'
    assert session.query(Ballot.vote_id.distinct()).one()[0] == 'vote'
    assert vote.ballots.count() == 2

    session.flush()
    assert session.query(Ballot.vote_id.distinct()).one()[0] == 'vote'
    assert vote.ballots.count() == 2


def test_vote_attachments(test_app, explanations_pdf):
    models = tuple(
        cls(
            title="Universal Healthcare",
            domain='federation',
            date=date(2015, 6, 14)
        ) for cls in (Vote, ComplexVote)
    )

    for model in models:
        assert model.explanations_pdf is None
        del model.explanations_pdf
        model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
        assert model.explanations_pdf.name == 'explanations_pdf'
        assert model.explanations_pdf.reference.filename == 'explanations.pdf'
        assert model.explanations_pdf.reference.content_type == \
            'application/pdf'
        del model.explanations_pdf
        assert model.explanations_pdf is None
