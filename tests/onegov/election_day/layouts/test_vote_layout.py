from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import BallotResult
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_vote_layout_general(session: Session) -> None:

    layout = VoteLayout(Vote(date=date(2021, 1, 1)), DummyRequest())  # type: ignore[arg-type]

    assert layout.all_tabs == (
        'entities',
        'districts',
        'statistics',
        'proposal-entities',
        'proposal-districts',
        'proposal-statistics',
        'counter-proposal-entities',
        'counter-proposal-districts',
        'counter-proposal-statistics',
        'tie-breaker-entities',
        'tie-breaker-districts',
        'tie-breaker-statistics',
        'data'
    )

    assert layout.title('undefined') == ''
    assert layout.title('entities') == '__entities'
    assert layout.title('districts') == '__districts'
    assert layout.title('statistics') == 'Statistics'
    assert layout.title('proposal-entities') == 'Proposal'
    assert layout.title('proposal-districts') == 'Proposal'
    assert layout.title('proposal-statistics') == 'Proposal'
    assert layout.title('counter-proposal-entities') == (
        'Direct Counter Proposal'
    )
    assert layout.title('counter-proposal-districts') == (
        'Direct Counter Proposal'
    )
    assert layout.title('counter-proposal-statistics') == (
        'Direct Counter Proposal'
    )
    assert layout.title('tie-breaker-entities') == 'Tie-Breaker'
    assert layout.title('tie-breaker-districts') == 'Tie-Breaker'
    assert layout.title('tie-breaker-statistics') == 'Tie-Breaker'
    assert layout.title('data') == 'Downloads'

    assert layout.subtitle('undefined') == ''
    assert layout.subtitle('entities') == ''
    assert layout.subtitle('districts') == ''
    assert layout.subtitle('statistics') == ''
    assert layout.subtitle('proposal-entities') == '__entities'
    assert layout.subtitle('proposal-districts') == '__districts'
    assert layout.subtitle('proposal-statistics') == 'Statistics'
    assert layout.subtitle('counter-proposal-entities') == '__entities'
    assert layout.subtitle('counter-proposal-districts') == '__districts'
    assert layout.subtitle('counter-proposal-statistics') == 'Statistics'
    assert layout.subtitle('tie-breaker-entities') == '__entities'
    assert layout.subtitle('tie-breaker-districts') == '__districts'
    assert layout.subtitle('tie-breaker-statistics') == 'Statistics'
    assert layout.subtitle('data') == ''

    layout = VoteLayout(Vote(), DummyRequest())  # type: ignore[arg-type]
    assert layout.type == 'simple'
    assert layout.main_view == 'Vote/entities'
    assert layout.ballot.type == 'proposal'
    assert layout.map_link == 'Vote/proposal-by-entities-map?locale=de'
    assert layout.table_link() == 'Vote/proposal-by-entities-table?locale=de'

    layout = VoteLayout(Vote(), DummyRequest(), tab='districts')  # type: ignore[arg-type]
    assert layout.map_link == 'Vote/proposal-by-districts-map?locale=de'
    assert layout.table_link() == 'Vote/proposal-by-districts-table?locale=de'

    layout = VoteLayout(
        ComplexVote(), DummyRequest(), tab='tie-breaker-entities'  # type: ignore[arg-type]
    )
    assert layout.type == 'complex'
    assert layout.main_view == 'ComplexVote/proposal-entities'
    assert layout.ballot.type == 'tie-breaker'
    assert layout.map_link == (
        'ComplexVote/tie-breaker-by-entities-map?locale=de'
    )
    assert layout.table_link() == (
        'ComplexVote/tie-breaker-by-entities-table?locale=de'
    )

    layout = VoteLayout(
        ComplexVote(), DummyRequest(), tab='tie-breaker-districts'  # type: ignore[arg-type]
    )
    assert layout.map_link == (
        'ComplexVote/tie-breaker-by-districts-map?locale=de'
    )
    assert layout.table_link() == (
        'ComplexVote/tie-breaker-by-districts-table?locale=de'
    )

    with freeze_time("2014-01-01 12:00"):
        vote = ComplexVote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        assert all((vote.proposal, vote.counter_proposal, vote.tie_breaker))
        session.add(vote)
        session.flush()

        ts = '1388577600'
        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        hp = vote.proposal.id
        hc = vote.counter_proposal.id
        ht = vote.tie_breaker.id

        request: Any = DummyRequest()
        request.app.filestorage = Mock()

        layout = VoteLayout(vote, request)
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-__entities.svg'

        layout = VoteLayout(vote, request, 'districts')
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-__districts.svg'
        assert layout.table_link() == (
            'ComplexVote/proposal-by-districts-table?locale=de'
        )
        assert layout.widget_link == 'ComplexVote/vote-header-widget'

        layout = VoteLayout(vote, request, 'proposal-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-proposal-__entities.svg'
        assert layout.table_link() == (
            'ComplexVote/proposal-by-entities-table?locale=de'
        )

        layout = VoteLayout(vote, request, 'proposal-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hp}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-proposal-__districts.svg'
        assert layout.table_link() == (
            'ComplexVote/proposal-by-districts-table?locale=de'
        )

        layout = VoteLayout(vote, request, 'counter-proposal-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == (
            'vote-direct-counter-proposal-__entities.svg'
        )
        assert layout.table_link() == (
            'ComplexVote/counter-proposal-by-entities-table?locale=de'
        )

        layout = VoteLayout(vote, request, 'counter-proposal-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{hc}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == (
            'vote-direct-counter-proposal-__districts.svg'
        )
        assert layout.table_link() == (
            'ComplexVote/counter-proposal-by-districts-table?locale=de'
        )

        layout = VoteLayout(vote, request, 'tie-breaker-entities')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.entities-map.de.svg'
        assert layout.svg_link == 'Ballot/entities-map-svg'
        assert layout.svg_name == 'vote-tie-breaker-__entities.svg'
        assert layout.table_link() == (
            'ComplexVote/tie-breaker-by-entities-table?locale=de'
        )

        layout = VoteLayout(vote, request, 'tie-breaker-districts')
        layout.has_districts = True
        assert layout.pdf_path == f'pdf/vote-{hv}.{ts}.de.pdf'
        assert layout.svg_path == f'svg/ballot-{ht}.{ts}.districts-map.de.svg'
        assert layout.svg_link == 'Ballot/districts-map-svg'
        assert layout.svg_name == 'vote-tie-breaker-__districts.svg'
        assert layout.table_link() == (
            'ComplexVote/tie-breaker-by-districts-table?locale=de'
        )


def test_vote_layout_menu(session: Session) -> None:
    vote = Vote(title='Vote', date=date(2000, 1, 1), domain='federation')
    session.add(vote)
    session.flush()

    request: Any = DummyRequest()
    assert VoteLayout(vote, request).menu == []
    assert VoteLayout(vote, request, 'data').menu == []

    vote.proposal.results.append(
        BallotResult(entity_id=1, name='1', counted=True)
    )
    assert VoteLayout(vote, request).menu == [
        ('__entities', 'Vote/entities', True, []),
        ('Statistics', 'Vote/statistics', False, []),
        ('Downloads', 'Vote/data', False, [])
    ]
    assert VoteLayout(vote, request, 'data').menu == [
        ('__entities', 'Vote/entities', False, []),
        ('Statistics', 'Vote/statistics', False, []),
        ('Downloads', 'Vote/data', True, [])
    ]

    request.app.principal.has_districts = True
    assert VoteLayout(vote, request).menu == [
        ('__entities', 'Vote/entities', True, []),
        ('__districts', 'Vote/districts', False, []),
        ('Statistics', 'Vote/statistics', False, []),
        ('Downloads', 'Vote/data', False, [])
    ]


def test_vote_layout_menu_complex(session: Session) -> None:
    vote = ComplexVote(
        title='Vote', date=date(2000, 1, 1), domain='federation'
    )
    session.add(vote)
    session.flush()

    request: Any = DummyRequest()
    assert VoteLayout(vote, request).menu == []
    assert VoteLayout(vote, request, 'data').menu == []

    vote.proposal.results.append(
        BallotResult(entity_id=1, name='1', counted=True)
    )
    assert VoteLayout(vote, request).menu == [
        (
            'Proposal',
            '',
            False,
            [
                ('__entities', 'ComplexVote/proposal-entities', False, []),
                ('Statistics', 'ComplexVote/proposal-statistics', False, [])
            ]
        ),
        (
            'Direct Counter Proposal',
            '',
            False,
            [
                ('__entities', 'ComplexVote/counter-proposal-entities',
                 False, []),
                ('Statistics', 'ComplexVote/counter-proposal-statistics',
                 False, [])
            ]
        ),
        (
            'Tie-Breaker',
            '',
            False,
            [
                ('__entities', 'ComplexVote/tie-breaker-entities', False, []),
                ('Statistics', 'ComplexVote/tie-breaker-statistics', False, [])
            ]
        ),
        ('Downloads', 'ComplexVote/data', False, [])
    ]

    request.app.principal.has_districts = True
    assert VoteLayout(vote, request).menu == [
        (
            'Proposal',
            '',
            False,
            [
                ('__entities', 'ComplexVote/proposal-entities', False, []),
                ('__districts', 'ComplexVote/proposal-districts', False, []),
                ('Statistics', 'ComplexVote/proposal-statistics', False, [])
            ]
        ),
        (
            'Direct Counter Proposal',
            '',
            False,
            [
                ('__entities', 'ComplexVote/counter-proposal-entities',
                 False, []),
                ('__districts', 'ComplexVote/counter-proposal-districts',
                 False, []),
                ('Statistics', 'ComplexVote/counter-proposal-statistics',
                 False, [])
            ]
        ),
        (
            'Tie-Breaker',
            '',
            False,
            [
                ('__entities', 'ComplexVote/tie-breaker-entities', False, []),
                ('__districts', 'ComplexVote/tie-breaker-districts',
                 False, []),
                ('Statistics', 'ComplexVote/tie-breaker-statistics', False, [])
            ]
        ),
        ('Downloads', 'ComplexVote/data', False, [])
    ]


def test_vote_layout_table_links() -> None:
    vote = Vote(date=date(2000, 1, 1), domain='federation')
    for tab, expected in (
        ('entities', 'Vote/proposal-by-entities-table'),
        ('proposal-entities', 'Vote/proposal-by-entities-table'),
        ('proposal-districts', 'Vote/proposal-by-districts-table'),
        ('counter-proposal-entities', 'Vote/proposal-by-entities-table'),
        ('counter-proposal-districts', 'Vote/proposal-by-districts-table'),
        ('tie-breaker-entities', 'Vote/proposal-by-entities-table'),
        ('tie-breaker-districts', 'Vote/proposal-by-districts-table'),
        ('data', None)
    ):
        layout = VoteLayout(vote, DummyRequest(), tab=tab)  # type: ignore[arg-type]
        assert not expected or f'{expected}?locale=de' == layout.table_link()
