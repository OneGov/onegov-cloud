from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import Screen
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_screen(session: Session) -> None:
    with freeze_time('2020-01-01 04:00'):
        election = Election(
            title='Election',
            domain='federation',
            date=date(2015, 6, 14)
        )
        session.add(election)
        session.flush()

    with freeze_time('2020-01-02 04:00'):
        screen = Screen(
            number=5,
            group='A',
            duration=10,
            type='majorz_election',
            structure='<title />',
            election_id=election.id,
            description='My Screen',
            css='h1 { font-size: 20em; }'
        )
        session.add(screen)
        session.flush()

    assert screen.number == 5
    assert screen.group == 'A'
    assert screen.duration == 10
    assert screen.type == 'majorz_election'
    assert screen.structure == '<title />'
    assert screen.vote is None
    assert screen.election == election
    assert screen.election_compound is None
    assert screen.election_compound_part is None
    assert screen.model == election
    assert screen.description == 'My Screen'
    assert screen.css == 'h1 { font-size: 20em; }'
    assert screen.screen_type.categories == (
        'generic', 'election', 'majorz_election'
    )
    assert screen.last_modified == datetime(2020, 1, 2, 4, tzinfo=timezone.utc)

    with freeze_time('2020-01-03 04:00'):
        screen.type = 'proporz_election'
        session.flush()

    assert screen.type == 'proporz_election'
    assert screen.vote is None
    assert screen.election == election
    assert screen.election_compound is None
    assert screen.election_compound_part is None
    assert screen.model == election
    assert screen.screen_type.categories == (
        'generic', 'election', 'proporz_election'
    )
    assert screen.last_modified == datetime(2020, 1, 3, 4, tzinfo=timezone.utc)

    with freeze_time('2020-01-04 04:00'):
        election_compound = ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2015, 6, 14),
        )
        session.add(election_compound)
        screen.election = None
        screen.election_compound = election_compound
        screen.type = 'election_compound'
        session.flush()

    assert screen.type == 'election_compound'
    assert screen.vote is None
    assert screen.election is None
    assert screen.election_compound == election_compound
    assert screen.model == election_compound
    assert screen.screen_type.categories == ('generic', 'election_compound')
    assert screen.last_modified == datetime(2020, 1, 4, 4, tzinfo=timezone.utc)

    election_compound_part = ElectionCompoundPart(
        election_compound, 'domain', 'segment'
    )
    screen.type = 'election_compound_part'
    screen.domain = 'domain'
    screen.domain_segment = 'segment'

    assert screen.type == 'election_compound_part'
    assert screen.vote is None
    assert screen.election is None
    assert screen.election_compound == election_compound
    assert screen.election_compound_part == election_compound_part
    assert screen.model == election_compound_part
    assert screen.screen_type.categories == ('generic', 'election_compound')
    assert screen.last_modified == datetime(2020, 1, 4, 4, tzinfo=timezone.utc)

    with freeze_time('2020-01-05 04:00'):
        vote = Vote(
            title='Vote',
            domain='canton',
            date=date(2015, 6, 14),
        )
        session.add(vote)
        screen.vote = vote
        screen.election = None
        screen.election_compound = None
        screen.type = 'simple_vote'
        session.flush()

    assert screen.type == 'simple_vote'
    assert screen.vote == vote
    assert screen.election is None
    assert screen.election_compound is None
    assert screen.election_compound_part is None
    assert screen.model == vote
    assert screen.screen_type.categories == ('generic', 'vote')
    assert screen.last_modified == datetime(2020, 1, 5, 4, tzinfo=timezone.utc)

    with freeze_time('2020-01-06 04:00'):
        screen.type = 'complex_vote'
        session.flush()

    assert screen.type == 'complex_vote'
    assert screen.vote == vote
    assert screen.election is None
    assert screen.election_compound is None
    assert screen.election_compound_part is None
    assert screen.model == vote
    assert screen.screen_type.categories == ('generic', 'vote', 'complex_vote')
    assert screen.last_modified == datetime(2020, 1, 6, 4, tzinfo=timezone.utc)


def test_screen_next(session: Session) -> None:
    screens = {
        number: Screen(
            number=number,
            group=group,
            type='majorz_election',
            structure='<title />',
        )
        for number, group in enumerate(
            (None, 'A', 'B', None, 'B', 'A', 'B', 'C')
        )
    }
    for screen in screens.values():
        session.add(screen)
    session.flush()

    assert screens[0].next is None
    assert screens[1].next == screens[5]
    assert screens[2].next == screens[4]
    assert screens[3].next is None
    assert screens[4].next == screens[6]
    assert screens[5].next == screens[1]
    assert screens[6].next == screens[2]
    assert screens[7].next is None
