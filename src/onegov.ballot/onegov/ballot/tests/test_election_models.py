from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election, ElectionResult, ListResult, CandidateResult


def test_election_create_all_models(session):
    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    election_result = ElectionResult(
        election_id=election.id,
        group='group',
        municipality_id=1000,
        elegible_voters=0,
        received_ballots=0,
        blank_ballots=0,
        invalid_ballots=0,
        blank_votes=0,
        invalid_votes=0
    )

    session.add(election_result)
    session.flush()

    list_result = ListResult(
        election_result_id=election_result.id,
        group='group',
        number_of_mandates=0,
        list_id='0',
        name='party',
        votes=0
    )

    session.add(list_result)
    session.flush()

    candidate_result = CandidateResult(
        election_result_id=election_result.id,
        elected=False,
        group='group',
        candidate_id='0',
        family_name='Moleman',
        first_name='Hans',
        votes=0
    )

    session.add(candidate_result)
    session.flush()


def test_election_id_generation(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election'


def test_election_summarized_properties(session):
    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=2
    )
    for x in range(1, 4):
        election.results.append(
            ElectionResult(
                group='group',
                municipality_id=x,
                elegible_voters=100 * x,
                received_ballots=80 * x,
                blank_ballots=4 * x,
                invalid_ballots=3 * x,
                blank_votes=2 * x,
                invalid_votes=x
            )
        )

    session.add(election)
    session.flush()

    assert election.elegible_voters == 600
    assert election.received_ballots == 480
    assert election.accounted_ballots == 438
    assert election.blank_ballots == 24
    assert election.invalid_ballots == 18
    assert election.accounted_votes == 858


def test_derived_properties(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )
    election.results.append(ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=100,
        received_ballots=50,
        blank_ballots=2,
        invalid_ballots=5,
        blank_votes=4,
        invalid_votes=3
    ))
    election.results.append(ElectionResult(
        group='group',
        municipality_id=2,
        elegible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    session.add(election)
    session.flush()

    assert election.results[0].unaccounted_ballots == 7
    assert election.results[0].accounted_ballots == 43
    assert election.results[0].turnout == 50.0
    assert election.results[1].unaccounted_ballots == 21
    assert election.results[1].accounted_ballots == 129
    assert election.results[1].turnout == 75.0
    assert election.unaccounted_ballots == 28
    assert election.accounted_ballots == 172
    assert int(election.turnout) == 66


def test_election_counted(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.counted == False

    election.total_municipalities = 2
    assert election.counted == False

    election.counted_municipalities = 1
    assert election.counted == False

    election.counted_municipalities = 2
    assert election.counted == True

    election.total_municipalities = 0
    assert election.counted == False

    election.total_municipalities = None
    assert election.counted == False


def test_election_last_result_change(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    with freeze_time("2015-01-01 12:00"):
        election.results.append(ElectionResult(
            group='group',
            municipality_id=1,
            elegible_voters=100,
            received_ballots=50,
            blank_ballots=2,
            invalid_ballots=5,
            blank_votes=4,
            invalid_votes=3
        ))

        session.flush()

    assert election.last_result_change.isoformat() == \
        '2015-01-01T12:00:00+00:00'

    with freeze_time("2015-01-01 13:00"):
        election.results.append(ElectionResult(
            group='group',
            municipality_id=2,
            elegible_voters=200,
            received_ballots=150,
            blank_ballots=6,
            invalid_ballots=15,
            blank_votes=12,
            invalid_votes=9
        ))

        session.flush()

    assert election.last_result_change.isoformat() == \
        '2015-01-01T13:00:00+00:00'


def test_election_results(session):
    election = Election(
        title='Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )

    session.add(election)
    session.flush()

    assert election.list_results == []
    assert election.candidate_results == []

    election_result_1 = ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election_result_2 = ElectionResult(
        group='group',
        municipality_id=2,
        elegible_voters=100,
        received_ballots=50,
        blank_ballots=1,
        invalid_ballots=0,
        blank_votes=8,
        invalid_votes=1
    )
    election.results.append(election_result_1)
    election.results.append(election_result_2)

    session.flush()

    assert election.list_results == []
    assert election.candidate_results == []

    election_result_1.candidates.append(
        CandidateResult(
            elected=True,
            group='group',
            candidate_id='1',
            list_id='1',
            list_name='Quimby Again!',
            family_name='Quimby',
            first_name='Joe',
            votes=520,
        )
    )
    election_result_1.candidates.append(
        CandidateResult(
            elected=False,
            group='group',
            candidate_id='2',
            list_id='2',
            list_name='Kwik-E-Major',
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            votes=111
        )
    )
    election_result_1.candidates.append(
        CandidateResult(
            elected=False,
            group='group',
            candidate_id='3',
            list_id='3',
            list_name='Partey',
            family_name='Flanders',
            first_name='Ned',
            votes=20
        )
    )
    election_result_1.candidates.append(
        CandidateResult(
            elected=False,
            group='group',
            candidate_id='4',
            list_id='3',
            list_name='Partey',
            family_name='Lovejoy',
            first_name='Tim',
            votes=1
        )
    )

    election_result_2.candidates.append(
        CandidateResult(
            elected=True,
            group='group',
            candidate_id='1',
            list_id='1',
            list_name='Quimby Again!',
            family_name='Quimby',
            first_name='Joe',
            votes=20
        )
    )
    election_result_2.candidates.append(
        CandidateResult(
            elected=False,
            group='group',
            candidate_id='5',
            list_id='3',
            list_name='Partey',
            family_name='Smithers',
            first_name='Waylon',
            votes=5
        )
    )

    session.flush()

    assert election.list_results == []
    assert sorted(election.candidate_results) == [
        ('1', 'Quimby', 'Joe', True, 'Quimby Again!', 540),
        ('2', 'Nahasapeemapetilon', 'Apu', False, 'Kwik-E-Major', 111),
        ('3', 'Flanders', 'Ned', False, 'Partey', 20),
        ('4', 'Lovejoy', 'Tim', False, 'Partey', 1),
        ('5', 'Smithers', 'Waylon', False, 'Partey', 5)
    ]

    election_result_1.lists.append(
        ListResult(
            group='group',
            number_of_mandates=1,
            list_id='1',
            name='Quimparty',
            votes=520
        )
    )
    election_result_1.lists.append(
        ListResult(
            group='group',
            number_of_mandates=0,
            list_id='2',
            name='Kwik-E-Major',
            votes=111
        )
    )
    election_result_1.lists.append(
        ListResult(
            group='group',
            number_of_mandates=0,
            list_id='3',
            name='Partey',
            votes=21
        )
    )
    election_result_2.lists.append(
        ListResult(
            group='group',
            number_of_mandates=1,
            list_id='1',
            name='Quimparty',
            votes=20
        )
    )
    election_result_2.lists.append(
        ListResult(
            group='group',
            number_of_mandates=0,
            list_id='3',
            name='Partey',
            votes=5
        )
    )

    session.flush()

    assert sorted(election.list_results) == [
        ('1', 'Quimparty', 540, 1),
        ('2', 'Kwik-E-Major', 111, 0),
        ('3', 'Partey', 26, 0)
    ]


def test_election_export(session):
    election = Election(
        title='Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )

    session.add(election)
    session.flush()

    assert election.export() == []

    election_result = ElectionResult(
        group='group',
        municipality_id=1,
        elegible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election_result.candidates.append(
        CandidateResult(
            elected=True,
            group='group',
            candidate_id='1',
            list_id='1',
            list_name='Quimby Again!',
            family_name='Quimby',
            first_name='Joe',
            votes=520,
        )
    )
    election_result.candidates.append(
        CandidateResult(
            elected=False,
            group='group',
            candidate_id='2',
            list_id='2',
            list_name='Kwik-E-Major',
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            votes=111
        )
    )

    election_result.lists.append(
        ListResult(
            group='group',
            number_of_mandates=1,
            list_id='1',
            name='Quimparty',
            votes=520
        )
    )
    election_result.lists.append(
        ListResult(
            group='group',
            number_of_mandates=0,
            list_id='2',
            name='Kwik-E-Major',
            votes=111
        )
    )
    election.results.append(election_result)

    session.flush()

    assert election.export() == [
        {
            'election_title': 'Election',
            'election_date': '2015-06-14',
            'election_type': 'majorz',
            'election_mandates': 1,
            'municipality_name': 'group',
            'municipality_bfs_number': 1,
            'municipality_elegible_voters': 1000,
            'municipality_received_ballots': 500,
            'municipality_blank_ballots': 10,
            'municipality_invalid_ballots': 5,
            'municipality_unaccounted_ballots': 15,
            'municipality_accounted_ballots': 485,
            'municipality_blank_votes': 80,
            'municipality_invalid_votes': 120,
            'municipality_accounted_votes': 285,
            'list_name': 'Quimparty',
            'list_votes': 520,
            'candidate_family_name': 'Quimby',
            'candidate_first_name': 'Joe',
            'candidate_elected': True,
            'candidate_votes': 520
        },
        {
            'election_title': 'Election',
            'election_date': '2015-06-14',
            'election_type': 'majorz',
            'election_mandates': 1,
            'municipality_name': 'group',
            'municipality_bfs_number': 1,
            'municipality_elegible_voters': 1000,
            'municipality_received_ballots': 500,
            'municipality_blank_ballots': 10,
            'municipality_invalid_ballots': 5,
            'municipality_unaccounted_ballots': 15,
            'municipality_accounted_ballots': 485,
            'municipality_blank_votes': 80,
            'municipality_invalid_votes': 120,
            'municipality_accounted_votes': 285,
            'list_name': 'Kwik-E-Major',
            'list_votes': 111,
            'candidate_family_name': 'Nahasapeemapetilon',
            'candidate_first_name': 'Apu',
            'candidate_elected': False,
            'candidate_votes': 111
        }
    ]
