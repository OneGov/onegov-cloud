from datetime import date
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.election_day.formats import export_vote_internal


def test_vote_export_internal(session):
    vote = ComplexVote(
        title="Abstimmung",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.title_translations['it_CH'] = 'Votazione'

    session.add(vote)
    session.flush()

    assert export_vote_internal(vote, ['de_CH']) == []

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

    assert export_vote_internal(vote, ['de_CH', 'fr_CH', 'it_CH']) == [
        {
            'id': "abstimmung",
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
            'id': "abstimmung",
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
            'id': "abstimmung",
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
