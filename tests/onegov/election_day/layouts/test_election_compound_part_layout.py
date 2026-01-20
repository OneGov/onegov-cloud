from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import PartyResult
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import DummyRequest
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_election_compound_part_layout_general(session: Session) -> None:
    date_ = date(2011, 1, 1)
    election = ProporzElection(  # type: ignore[misc]
        title="election",
        domain='region',
        domain_segment='Allschwil',
        domain_supersegment='Region 1',
        date=date_
    )
    session.add(election)
    session.add(ElectionCompound(title="e", domain='canton', date=date_))
    session.flush()
    compound = session.query(ElectionCompound).one()
    part = ElectionCompoundPart(compound, 'superregion', 'Region 1')
    request: Any = DummyRequest()
    layout = ElectionCompoundPartLayout(part, request)
    assert layout.all_tabs == (
        'districts',
        'candidates',
        'party-strengths',
        'statistics',
    )
    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('districts') == '__districts'
    assert layout.title('candidates') == 'Elected candidates'
    assert layout.title('party-strengths') == 'Party strengths'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.main_view == 'ElectionCompoundPart/districts'
    assert layout.majorz is False
    assert layout.proporz is True
    assert layout.has_party_results is False
    assert layout.tab_visible('statistics') is False

    # test results
    compound.elections = [election]
    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    layout = ElectionCompoundPartLayout(part, DummyRequest())  # type: ignore[arg-type]
    assert layout.has_results

    # test party results
    compound.party_results.append(
        PartyResult(
            domain='superregion',
            domain_segment='Region 1',
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    layout = ElectionCompoundPartLayout(part, DummyRequest())  # type: ignore[arg-type]
    assert layout.has_party_results is True

    # test main view
    layout = ElectionCompoundPartLayout(part, request)
    assert layout.main_view == 'ElectionCompoundPart/districts'

    compound.show_party_strengths = True
    layout = ElectionCompoundPartLayout(part, request)
    assert layout.main_view == 'ElectionCompoundPart/districts'

    compound.horizontal_party_strengths = True
    layout = ElectionCompoundPartLayout(part, request)
    assert layout.main_view == 'ElectionCompoundPart/party-strengths'

    # test file paths
    with freeze_time("2014-01-01 12:00"):
        compound = ElectionCompound(
            title="ElectionCompound",
            domain='canton',
            date=date(2011, 1, 1),
        )
        session.add(compound)
        session.flush()
        part = ElectionCompoundPart(compound, 'superregion', 'Region 1')
        hs = '2ef359817c8f8a7354e201f891cd7c11a13f4e025aa25239c3ad0cabe58bc49b'
        ts = '1388577600'

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = ElectionCompoundPartLayout(part, request, 'party-strengths')
        assert layout.svg_path == (
            f'svg/elections-{hs}-region-1.{ts}.party-strengths.de.svg'
        )
        assert layout.svg_link == 'ElectionCompoundPart/party-strengths-svg'
        assert layout.svg_name == (
            'electioncompound-region-1-party-strengths.svg'
        )

    # test table links
    for tab, expected in (
        ('districts', 'ElectionCompoundPart/districts-table'),
        ('candidates', 'ElectionCompoundPart/candidates-table'),
        ('party-strengths', 'ElectionCompoundPart/party-strengths-table'),
        ('statistics', 'ElectionCompoundPart/statistics-table')
    ):
        layout = ElectionCompoundPartLayout(part, DummyRequest(), tab=tab)  # type: ignore[arg-type]
        assert not expected or f'{expected}?locale=de' == layout.table_link()


def test_election_compound_part_layout_menu(session: Session) -> None:
    election = ProporzElection(  # type: ignore[misc]
        title="Election",
        domain='region',
        domain_segment='Allschwil',
        domain_supersegment='Region 1',
        date=date(2011, 1, 1)
    )
    compound = ElectionCompound(
        title="Elections",
        domain='canton',
        date=date(2011, 1, 1)
    )
    session.add(election)
    session.add(compound)
    session.flush()
    compound.elections = [election]
    part = ElectionCompoundPart(compound, 'superregion', 'Region 1')

    # No results yet
    request: Any = DummyRequest()
    assert ElectionCompoundPartLayout(part, request).menu == []
    assert ElectionCompoundPartLayout(part, request, 'data').menu == []

    # Results available
    election.results.append(
        ElectionResult(
            name='1',
            entity_id=1,
            counted=True,
            eligible_voters=500,
        )
    )
    assert ElectionCompoundPartLayout(part, request).menu == [
        ('__districts', 'ElectionCompoundPart/districts', False, []),
        ('Elected candidates', 'ElectionCompoundPart/candidates', False, []),
        ('Election statistics', 'ElectionCompoundPart/statistics', False, []),
    ]
    assert ElectionCompoundPartLayout(part, request, 'statistics').menu == [
        ('__districts', 'ElectionCompoundPart/districts', False, []),
        ('Elected candidates', 'ElectionCompoundPart/candidates', False, []),
        ('Election statistics', 'ElectionCompoundPart/statistics', True, []),
    ]

    # Party results available, but no views enabled
    compound.party_results.append(
        PartyResult(
            domain='superregion',
            domain_segment='Region 1',
            year=2017,
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'de_CH': 'A'},
            party_id='1'
        )
    )
    assert ElectionCompoundPartLayout(part, request).menu == [
        ('__districts', 'ElectionCompoundPart/districts', False, []),
        ('Elected candidates', 'ElectionCompoundPart/candidates', False, []),
        ('Election statistics', 'ElectionCompoundPart/statistics', False, []),
    ]

    # All views enabled
    compound.show_party_strengths = True
    compound.horizontal_party_strengths = True
    assert ElectionCompoundPartLayout(part, request).menu == [
        ('Party strengths', 'ElectionCompoundPart/party-strengths', False, []),
        ('__districts', 'ElectionCompoundPart/districts', False, []),
        ('Elected candidates', 'ElectionCompoundPart/candidates', False, []),
        ('Election statistics', 'ElectionCompoundPart/statistics', False, []),
    ]
