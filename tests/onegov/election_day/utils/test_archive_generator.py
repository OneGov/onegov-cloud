from __future__ import annotations

from collections import Counter
from datetime import date
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import BallotResult
from onegov.election_day.models import Municipality
from onegov.election_day.models import Vote
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.archive_generator import ArchiveGenerator
from zipfile import ZipFile, Path as ZipPath


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path
    from ..conftest import ImportTestDatasets, TestApp


def test_query_only_counted_votes_that_have_results(
    election_day_app_zg: TestApp
) -> None:

    archive_generator = ArchiveGenerator(election_day_app_zg)
    session = election_day_app_zg.session()

    sample_votes = [
        Vote(title="Abstimmung 1. Januar 2022", domain='federation',
             date=date(2022, 1, 1)),
        Vote(title="Abstimmung 2. Januar 2013", domain='federation',
             date=date(2013, 1, 2))
    ]

    ballot_results = [
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=7000, nays=3000, empty=0, invalid=0
        ),
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=2000, nays=5000, empty=0, invalid=0
        )
    ]
    # 2 Votes with 1 BallotResult each
    for sample_vote, ballot_result in zip(sample_votes, ballot_results):
        session.add(sample_vote)
        vote = session.query(Vote).filter_by(date=sample_vote.date).first()
        assert vote is not None
        vote.proposal.results.append(ballot_result)

    bern = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    target = ArchivedResult()
    source = ArchivedResult(type='vote')
    add_local_results(source, target, bern, session)
    session.flush()

    votes = archive_generator.all_counted_votes_with_results()
    assert len(votes) == 1


def test_archive_generation_from_scratch(election_day_app_zg: TestApp) -> None:
    archive_generator = ArchiveGenerator(election_day_app_zg)
    session = election_day_app_zg.session()

    sample_votes = [
        Vote(title="Abstimmung 1. Januar 2022", domain='federation',
             date=date(2022, 1, 1)),
        Vote(title="Abstimmung 1. Januar 2013", domain='federation',
             date=date(2013, 1, 1)),
        Vote(title="Abstimmung 2. Januar 2013", domain='federation',
             date=date(2013, 1, 2))
    ]

    ballot_results = [
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=7000, nays=3000, empty=0, invalid=0
        ),
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=3000, nays=7000, empty=0, invalid=0
        ),
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=2000, nays=5000, empty=0, invalid=0
        )
    ]
    # 3 Votes with 1 BallotResult each
    for sample_vote, ballot_result in zip(sample_votes, ballot_results):
        session.add(sample_vote)
        vote = session.query(Vote).filter_by(date=sample_vote.date).first()
        assert vote is not None
        vote.proposal.results.append(ballot_result)

    bern = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    target = ArchivedResult()
    source = ArchivedResult(type='vote')
    add_local_results(source, target, bern, session)
    session.flush()

    votes = archive_generator.all_counted_votes_with_results()

    assert votes[0].date == date(2022, 1, 1)
    assert votes[1].date == date(2013, 1, 2)
    assert votes[2].date == date(2013, 1, 1)

    grouped_by_year = archive_generator.group_by_year(votes)

    assert grouped_by_year[0][0].id == votes[0].id
    assert grouped_by_year[1][0].id == votes[1].id
    assert grouped_by_year[1][1].id == votes[2].id

    for item in grouped_by_year[1]:
        assert str(item.date.year) == "2013"

    for item in grouped_by_year[0]:
        assert str(item.date.year) == "2022"

    zip_path = archive_generator.generate_archive()
    assert zip_path is not None

    with (
        archive_generator.archive_dir.open(zip_path, mode="rb") as fi,
        ZipFile(fi) as zf
    ):
        path = ZipPath(zf)
        assert {p.name for p in (path / 'votes').iterdir()} == {
            "all_votes.csv", "2022", "2013"
        }

        counter: Counter[str] = Counter()
        total_bytes_csv = 0
        for info in zf.infolist():
            if info.is_dir():
                continue
            if not info.filename.startswith('votes/'):
                continue

            counter[info.filename.rsplit('/', 1)[-1]] += 1
            total_bytes_csv += info.file_size

        # We expect 3 csv because we have 3 votes,
        # Plus a csv that contains everything = 4
        assert sum(counter.values()) == 4
        assert total_bytes_csv > 10  # check to ensure files are not empty


def test_zipping_multiple_directories(
    election_day_app_zg: TestApp,
    tmp_path: Path
) -> None:
    archive_generator = ArchiveGenerator(election_day_app_zg)

    root = tmp_path / 'test1'
    root.mkdir()
    votes = (root / 'votes')
    votes.mkdir()
    elections = (root / 'elections')
    elections.mkdir()
    for year in ('2020', '2021', '2022'):
        year_dir = (votes / year)
        year_dir.mkdir()
        (year_dir / 'testfile-votes.csv').touch()
    (elections / '2022').mkdir()
    (elections / '2022' / 'testfile-elections.csv').touch()
    zip_path = archive_generator.zip_dir(str(root))

    archive_generator.include_docs(str(root))
    zip_path = archive_generator.zip_dir(str(root))

    with (
        archive_generator.archive_dir.open(zip_path, mode="rb") as fi,
        ZipFile(fi) as zf
    ):
        additional_files = [
            info
            for info in zf.infolist()
            if info.filename.endswith('.md')
        ]

        assert len(additional_files) != 0
        for info in additional_files:
            assert info.file_size > 100


def test_long_filenames_are_truncated(election_day_app_zg: TestApp) -> None:
    long_title = (
        "Bundesbeschluss vom 28. September 2018 über die "
        "Genehmigung und die Umsetzung des Notenaustauschs zwischen "
        "der Schweiz und der EU betreffend die Übernahme der "
        "Richtlinie (EU) 2017 /853 zur Änderung der "
        "EU-Waffenrichtlinie (Weiterentwicklung des Schengen "
        "Besitzstands) "
    )

    session = election_day_app_zg.session()
    session.add(Vote(title=long_title, domain='federation',
                     date=date(2022, 1, 1)))
    session.flush()
    vote = session.query(Vote).one()

    vote.proposal.results.append(BallotResult(
        name='Bern', entity_id=351,
        counted=True, yeas=7000, nays=3000, empty=0, invalid=0
    ))
    session.flush()

    bern = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    target = ArchivedResult()
    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)

    archive_generator = ArchiveGenerator(election_day_app_zg)

    zip_path = archive_generator.generate_archive()
    assert zip_path is not None
    with (
        archive_generator.archive_dir.open(zip_path, mode="rb") as fi,
        ZipFile(fi) as zf
    ):
        path = ZipPath(zf)
        first_file = next((path / 'votes' / '2022').iterdir())
        filename = first_file.name
        assert "bundesbeschluss-vom-28-september" in filename
        assert len(filename) <= archive_generator.MAX_FILENAME_LENGTH + 4


def test_election_generation(
    election_day_app_zg: TestApp,
    import_test_datasets: ImportTestDatasets
) -> None:

    results = import_test_datasets(
        'internal',
        'election',
        'zg',
        'canton',
        'proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=3,
        dataset_name='nationalratswahlen-2015',
        app_session=election_day_app_zg.session()
    )
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    results_ = import_test_datasets(
        'internal',
        'parties',
        'zg',
        'canton',
        election=election,
        dataset_name='nationalratswahlen-2015-parteien',
    )
    assert len(results_) == 1
    errors_ = next(iter(results_.values()))
    assert not errors_

    archive_generator = ArchiveGenerator(election_day_app_zg)
    zip_path = archive_generator.generate_archive()
    assert zip_path is not None
    with (
        archive_generator.archive_dir.open(zip_path, mode="rb") as fi,
        ZipFile(fi) as zf
    ):
        path = ZipPath(zf)
        assert 'elections' in [p.name for p in path.iterdir()]
        assert {p.name for p in (path / 'elections').iterdir()} == {'2015'}
        assert {p.name for p in (path / 'elections' / '2015').iterdir()} == {
            'proporz_internal_nationalratswahlen-2015.csv',
            'proporz_internal_nationalratswahlen-2015-parties.csv'
        }
