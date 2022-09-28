from functools import reduce
from onegov.ballot import Vote, BallotResult
from onegov.core.utils import module_path
from onegov.election_day.models import Municipality, ArchivedResult
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.archive_generator import ArchiveGenerator
from datetime import date
from fs.walk import Walker
from collections import Counter
from fs.zipfs import ReadZipFS
from fs.tempfs import TempFS
from fs.copy import copy_dir
from fs.osfs import OSFS


def test_votes_generation_group_by_year(election_day_app_zg_with_votes):
    archive_generator = ArchiveGenerator(election_day_app_zg_with_votes)

    votes = archive_generator.all_votes()

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


def test_votes_generation_csv(election_day_app_zg_with_votes):
    archive_generator = ArchiveGenerator(election_day_app_zg_with_votes)
    base_dir = archive_generator.generate_votes_csv()
    votes_dir = base_dir.listdir('votes')
    years = [str(year) for year in votes_dir]

    assert len(base_dir.listdir('votes')) == 2
    assert {"2022", "2013"} == set(years)

    votes = base_dir.opendir('votes')
    counter = Counter()
    total_bytes_csv = 0
    walker = Walker()
    for _, _, files in walker.walk(votes, namespaces=["basic", "details"]):
        for file in files:
            counter[file.name] += 1

        total_bytes_csv = sum(info.size for info in files)
    assert sum(counter.values()) == 3
    assert total_bytes_csv > 10  # check to ensure files are not empty


def test_zipping_multiple_directories(election_day_app_zg):
    archive_generator = ArchiveGenerator(election_day_app_zg)

    test_data = module_path("tests.onegov.election_day",
                            "fixtures/archive_generator/")

    native_filesystem = OSFS(test_data)
    tmp_fs = TempFS()
    copy_dir(
        src_fs=native_filesystem,
        src_path="test_data",
        dst_fs=tmp_fs,
        dst_path="test_data",
    )

    test_data_dir = tmp_fs.opendir("/test_data")
    f, _ = archive_generator.zip_dir(test_data_dir)

    with test_data_dir.open(f, mode="rb") as fi:
        with ReadZipFS(fi) as zip_fs:
            # roundtrip: extract zipfile again and validate it's internal
            # structure
            top_level_dir = zip_fs.listdir(".")
            assert "votes" in top_level_dir
            assert "elections" in top_level_dir

            votes = zip_fs.opendir("votes")
            elections = zip_fs.opendir("elections")

            votes_by_year = [year for year in votes.listdir(".")]
            elections_by_year = [year for year in elections.listdir(".")]

            assert {"2020", "2021", "2022"} == set(votes_by_year)
            assert {"2022"} == set(elections_by_year)

            votes_csv_files = [
                [csv for csv in zip_fs.scandir(f"votes/{year}")]
                for year in votes_by_year
            ]

            flattened = reduce(lambda x, y: x + y, votes_csv_files)
            assert len(flattened) == 6

            election_csv_files = [
                [csv for csv in zip_fs.scandir(f"elections/{year}")]
                for year in elections_by_year
            ]

            flattened = reduce(lambda x, y: x + y, election_csv_files)
            assert len(flattened) == 2

            additional_files = (match for match in zip_fs.glob(
                "*.md", namespaces=["details"]))

            assert len(list(additional_files)) >= 5
            for f in additional_files:
                assert f.info.size > 100


def test_long_filenames_are_truncated(election_day_app_zg):
    long_title = "Bundesbeschluss vom 28. September 2018 über die "\
                 "Genehmigung und die Umsetzung des Notenaustauschs zwischen "\
                 "der Schweiz und der EU betreffend die Übernahme der "\
                 "Richtlinie (EU) 2017 /853 zur Änderung der "\
                 "EU-Waffenrichtlinie (Weiterentwicklung des Schengen "\
                 "Besitzstands) "

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

    bern = Municipality(name='Bern', municipality='351')
    target = ArchivedResult()
    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)

    generator = ArchiveGenerator(election_day_app_zg)

    base_dir = generator.generate_votes_csv()

    csv = [csv for csv in base_dir.scandir("votes/2022", namespaces=["basic"])]
    first_file = csv[0]

    assert "bundesbeschluss-vom-28-september" in first_file.name


def test_election_generation(election_day_app_zg, import_test_datasets):
    import_test_datasets(
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

    archive_generator = ArchiveGenerator(election_day_app_zg)
    archive_dir = archive_generator.generate_elections_csv()
    temp_path, _ = archive_generator.zip_dir(archive_dir)

    with archive_dir.open(temp_path, mode="rb") as fi:
        with ReadZipFS(fi) as zip_fs:
            top_level_dir = zip_fs.listdir(".")
            assert "elections" in top_level_dir

            elections = zip_fs.opendir("elections")
            elections_by_year = [year for year in elections.listdir(".")]

            assert {"2015"} == set(elections_by_year)

            csv = [csv for csv in zip_fs.scandir("elections/2015",
                                                 namespaces=["basic"])]
            first_file = csv[0]

            assert "proporz_internal_nationalratswahlen-2015.csv" ==\
                   first_file.name


def test_generate_archive_total_package(election_day_app_zg_with_votes):
    app = election_day_app_zg_with_votes

    generator = ArchiveGenerator(app)
    base_dir, archive_zip = generator.generate_archive()

    assert base_dir.exists(archive_zip)
    file_size = base_dir.getinfo(archive_zip, namespaces=['details']).size
    assert file_size > 10  # ensure file is not 0 bytes


def test_get_docs_files_at_runtime():
    docs = module_path("onegov.election_day", "static/docs/")

    docs_dir = OSFS(docs)
    assert docs_dir.isdir("api")
    assert not docs_dir.isempty("api")
    languages = ["de", "en", "it", "fr", "rm"]
    api = docs_dir.opendir("api")
    assert all(api.isfile(f"open_data_{l}.md") for l in languages)


def test_open_data_markdown_files_are_included(election_day_app_zg_with_votes):
    app = election_day_app_zg_with_votes

    generator = ArchiveGenerator(app)
    archive_dir, zip_dir = generator.generate_archive()
    doc_files = generator.additional_files_to_include

    with archive_dir.open(zip_dir, mode="rb") as fi:
        with ReadZipFS(fi) as zip_fs:
            top_level_dir = zip_fs.listdir(".")
            assert all(file in top_level_dir for file in doc_files)
