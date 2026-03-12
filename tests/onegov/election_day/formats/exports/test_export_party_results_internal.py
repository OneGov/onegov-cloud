from __future__ import annotations

from datetime import date
from decimal import Decimal
from onegov.election_day.formats import export_parties_internal
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import PartyPanachageResult
from onegov.election_day.models import PartyResult
from onegov.election_day.models import ProporzElection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_proporz_election_export_parties(session: Session) -> None:
    session.add(
        ProporzElection(
            title='Wahl',
            domain='federation',
            date=date(2016, 6, 14),
            number_of_mandates=1,
            absolute_majority=144
        )
    )
    session.flush()
    election = session.query(ProporzElection).one()
    election.colors = {
        'Conservative': 'red',
        'Libertarian': 'black'
    }

    assert export_parties_internal(election, ['en_US'], 'en_US') == []

    # Add party results
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=0,
            votes=0,
            voters_count=Decimal('1.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='2',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=2,
            votes=2,
            voters_count=Decimal('3.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Libertarian'},
            party_id='2',
            year=2016
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('2.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2012
        )
    )
    election.party_results.append(
        PartyResult(
            domain='federation',
            number_of_mandates=3,
            votes=3,
            voters_count=Decimal('4.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2016
        )
    )
    election.party_results.append(
        PartyResult(
            domain='quarter',
            domain_segment='Quarter 1',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('4.01'),
            voters_count_percentage=Decimal('50.02'),
            total_votes=50,
            name_translations={'en_US': 'Conservative'},
            party_id='1',
            year=2016
        )
    )
    assert export_parties_internal(
        election, ['en_US', 'de_CH'], 'en_US'
    ) == [
        {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'red',
            'mandates': 3,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'black',
            'mandates': 2,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '2',
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'year': 2012,
        }, {
            'domain': 'federation',
            'domain_segment': None,
            'color': 'black',
            'mandates': 0,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '2',
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'year': 2012,
        }, {
            'domain': 'quarter',
            'domain_segment': 'Quarter 1',
            'color': 'red',
            'mandates': 1,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 1,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
        }
    ]

    for idx, source in enumerate(('1', '2', '3', '')):
        election.party_panachage_results.append(
            PartyPanachageResult(
                target='1',
                source=source,
                votes=idx + 1
            )
        )
    election.party_panachage_results.append(
        PartyPanachageResult(
            target='2',
            source='1',
            votes=5,
        )
    )
    assert export_parties_internal(
        election, ['de_CH', 'en_US'], 'de_CH'
    ) == [
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '1',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_1': 1,
            'panachage_votes_from_2': 2,
            'panachage_votes_from_999': 4,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '2',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_1': 5,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '1',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'federation',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '2',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_1': None,
            'panachage_votes_from_2': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'quarter',
            'domain_segment': 'Quarter 1',
            'color': 'red',
            'mandates': 1,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '1',
            'total_votes': 50,
            'votes': 1,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'year': 2016,
            'panachage_votes_from_1': None,
            'panachage_votes_from_999': None,
        }
    ]


def test_election_compound_export_parties(session: Session) -> None:
    session.add(
        ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2016, 6, 14),
        )
    )
    session.flush()
    election_compound = session.query(ElectionCompound).one()
    election_compound.colors = {
        'Conservative': 'red',
        'Libertarian': 'black'
    }

    assert export_parties_internal(election_compound, ['de_CH'], 'de_CH') == []

    # Add party results
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=0,
            votes=0,
            voters_count=Decimal('1.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='3',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=2,
            votes=2,
            voters_count=Decimal('3.01'),
            total_votes=50,
            voters_count_percentage=Decimal('50.02'),
            name_translations={'en_US': 'Libertarian'},
            party_id='3',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('2.01'),
            total_votes=100,
            voters_count_percentage=Decimal('100.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=3,
            votes=3,
            voters_count=Decimal('4.01'),
            total_votes=50,
            voters_count_percentage=Decimal('50.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='superregion',
            domain_segment='Superregion 1',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('1.01'),
            total_votes=10,
            voters_count_percentage=Decimal('10.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='region',
            domain_segment='Region 1',
            number_of_mandates=10,
            votes=10,
            voters_count=Decimal('1.01'),
            total_votes=10,
            voters_count_percentage=Decimal('10.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )

    assert export_parties_internal(
        election_compound, ['en_US', 'de_CH'], 'en_US'
    ) == [
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '3',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '3',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
        },
        {
            'domain': 'region',
            'domain_segment': 'Region 1',
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 10,
            'total_votes': 10,
            'votes': 10,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
        },
        {
            'domain': 'superregion',
            'domain_segment': 'Superregion 1',
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 10,
            'votes': 1,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
        },
    ]

    # Add panachage results
    for idx, source in enumerate(('5', '3', '0', '')):
        election_compound.party_panachage_results.append(
            PartyPanachageResult(
                target='5',
                source=source,
                votes=idx + 1
            )
        )
    election_compound.party_panachage_results.append(
        PartyPanachageResult(
            target='3',
            source='5',
            votes=5,
        )
    )
    assert export_parties_internal(
        election_compound, ['de_CH', 'en_US'], 'de_CH'
    ) == [
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '3',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': 5,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '5',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_3': 2,
            'panachage_votes_from_5': 1,
            'panachage_votes_from_999': 4,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '3',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'region',
            'domain_segment': 'Region 1',
            'year': 2016,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 10,
            'total_votes': 10,
            'votes': 10,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'superregion',
            'domain_segment': 'Superregion 1',
            'year': 2016,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 10,
            'votes': 1,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
    ]
