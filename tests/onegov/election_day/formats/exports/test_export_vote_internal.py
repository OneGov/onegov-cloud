from __future__ import annotations

from datetime import date
from onegov.election_day.formats import export_vote_internal
from onegov.election_day.models import BallotResult
from onegov.election_day.models import ComplexVote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_vote_export_internal(session: Session) -> None:
    vote = ComplexVote(
        title="Abstimmung",
        short_title="A",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.title_translations['it_CH'] = 'Votazione'  # type: ignore[index]
    vote.short_title_translations['it_CH'] = 'V'  # type: ignore[index]
    vote.counter_proposal.title_translations = {
        'de_CH': 'Gegenvorschlag',
        'it_CH': 'Controprogetto'
    }
    vote.tie_breaker.title_translations = {
        'de_CH': 'Stichfrage',
        'it_CH': 'Spareggio'
    }
    session.add(vote)
    session.flush()

    assert export_vote_internal(vote, ['de_CH']) == []

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
            'id': "a",
            'title_de_CH': "Gegenvorschlag",
            'title_fr_CH': "",
            'title_it_CH': "Controprogetto",
            'short_title_de_CH': "A",
            'short_title_fr_CH': "",
            'short_title_it_CH': "V",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'ballot_answer': None,
            'answer': None,
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
        },
        {
            'id': "a",
            'title_de_CH': "Abstimmung",
            'title_fr_CH': "",
            'title_it_CH': "Votazione",
            'short_title_de_CH': "A",
            'short_title_fr_CH': "",
            'short_title_it_CH': "V",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'ballot_answer': None,
            'answer': None,
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
            'id': "a",
            'title_de_CH': "Abstimmung",
            'title_fr_CH': "",
            'title_it_CH': "Votazione",
            'short_title_de_CH': "A",
            'short_title_fr_CH': "",
            'short_title_it_CH': "V",
            'date': "2015-06-14",
            'shortcode': "FOO",
            'domain': "federation",
            'status': "unknown",
            'ballot_answer': None,
            'answer': None,
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
    ]
