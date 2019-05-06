import os
import yaml

from click.testing import CliRunner
from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.pdf import Pdf
from onegov.swissvotes.cli import cli
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import SwissVoteFile
from pathlib import Path
from psycopg2.extras import NumericRange
from transaction import commit


def write_config(path, postgres_dsn, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/onegov_swissvotes/*',
                'application': 'onegov.swissvotes.SwissvotesApp',
                'namespace': 'onegov_swissvotes',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'depot_backend': 'depot.io.local.LocalFileStorage',
                    'depot_storage_path': temporary_directory,
                    # 'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    },
                },
            }
        ]
    }
    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))


def run_command(cfg_path, principal, commands, input=None):
    runner = CliRunner()
    return runner.invoke(
        cli,
        [
            '--config', cfg_path,
            '--select', '/onegov_swissvotes/{}'.format(principal),
        ] + commands,
        input
    )


def test_add_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 1
    assert "This selector may not reference an existing path" in result.output


def test_delete_instance(postgres_dsn, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, postgres_dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'n')
    assert result.exit_code == 1
    assert "Deletion process aborted" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'y')
    assert result.exit_code == 0
    assert "Instance was deleted successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['delete'], 'y')
    assert result.exit_code == 1
    assert "Selector doesn't match any paths, aborting." in result.output


def test_import_attachments(session_manager, temporary_directory, redis_url):

    def create_file(path, content='content'):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as file:
            pdf = Pdf(file)
            pdf.init_report()
            pdf.p(content)
            pdf.generate()

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    # Test parsing
    folder = Path(temporary_directory) / 'data-1'
    create_file(folder / 'voting_text' / 'de_CH' / '001.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '01.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '1.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '1.1.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '01.1.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '01.10.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '001.100.pdf')

    create_file(folder / 'voting_text' / 'de_CH' / 'a.pdf')
    create_file(folder / 'voting_text' / 'de_CH' / '100.pdx')
    create_file(folder / 'voting_text' / 'rm_CH' / '100.pdf')
    create_file(folder / 'voting_text' / '100.pdf')
    create_file(folder / 'another_text' / 'de_CH' / '100.pdf')
    create_file(folder / 'another_text' / '100.pdf')
    create_file(folder / '100.pdf')

    result = run_command(cfg_path, 'govikon', ['import', str(folder)])
    assert result.exit_code == 0

    assert "1 for voting_text/de_CH/001.pdf" in result.output
    assert "1 for voting_text/de_CH/01.pdf" in result.output
    assert "1 for voting_text/de_CH/1.pdf" in result.output
    assert "1.1 for voting_text/de_CH/1.1.pdf" in result.output
    assert "1.1 for voting_text/de_CH/01.1.pdf" in result.output
    assert "1.10 for voting_text/de_CH/01.10.pdf" in result.output
    assert "1.100 for voting_text/de_CH/001.100.pdf" in result.output

    assert "Invalid name voting_text/de_CH/a.pdf" in result.output
    assert "Ignoring voting_text/de_CH/100.pdx" in result.output
    assert "Ignoring /another_text" in result.output
    assert "Ignoring /voting_text/rm_CH" in result.output
    assert "Ignoring /voting_text/100.pdf" in result.output
    assert "Ignoring /another_text" in result.output
    assert "Ignoring /100.pdf" in result.output

    # Test importing
    folder = Path(temporary_directory) / 'data-2'
    for name in (
        'federal_council_message',
        'parliamentary_debate',
        'realization',
        'resolution',
        'voting_booklet',
        'voting_text',
    ):
        create_file(folder / name / 'de_CH' / '1.0.pdf', f"A 1{name}de end")
        create_file(folder / name / 'fr_CH' / '1.0.pdf', f"B 1{name}fr end")
        create_file(folder / name / 'de_CH' / '2.0.pdf', f"C 2{name}de end")
        create_file(folder / name / 'fr_CH' / '2.0.pdf', f"D 2{name}fr end")

    session_manager.ensure_schema_exists('onegov_swissvotes-govikon')
    session_manager.set_current_schema('onegov_swissvotes-govikon')
    session = session_manager.session()
    for number in (1, 2, 3):
        session.add(
            SwissVote(
                id=number,
                bfs_number=Decimal(str(number)),
                date=date(1990, 6, 2),
                decade=NumericRange(1990, 1999),
                legislation_number=4,
                legislation_decade=NumericRange(1990, 1994),
                title_de=f"Vote {number}",
                title_fr=f"Vote {number}",
                short_title_de=f"Vote {number}",
                short_title_fr=f"Vote {number}",
                votes_on_same_day=3,
                _legal_form=1,
            )
        )
        session.flush()
    commit()

    result = run_command(cfg_path, 'govikon', ['import', str(folder)])
    assert result.exit_code == 0
    assert "Added federal_council_message/de_CH/1.0.pdf" in result.output
    assert "Added federal_council_message/de_CH/2.0.pdf" in result.output
    assert "Added federal_council_message/fr_CH/1.0.pdf" in result.output
    assert "Added federal_council_message/fr_CH/2.0.pdf" in result.output
    assert "Added parliamentary_debate/de_CH/1.0.pdf" in result.output
    assert "Added parliamentary_debate/de_CH/2.0.pdf" in result.output
    assert "Added parliamentary_debate/fr_CH/1.0.pdf" in result.output
    assert "Added parliamentary_debate/fr_CH/2.0.pdf" in result.output
    assert "Added realization/de_CH/1.0.pdf" in result.output
    assert "Added realization/de_CH/2.0.pdf" in result.output
    assert "Added realization/fr_CH/1.0.pdf" in result.output
    assert "Added realization/fr_CH/2.0.pdf" in result.output
    assert "Added resolution/de_CH/1.0.pdf" in result.output
    assert "Added resolution/de_CH/2.0.pdf" in result.output
    assert "Added resolution/fr_CH/1.0.pdf" in result.output
    assert "Added resolution/fr_CH/2.0.pdf" in result.output
    assert "Added voting_booklet/de_CH/1.0.pdf" in result.output
    assert "Added voting_booklet/de_CH/2.0.pdf" in result.output
    assert "Added voting_booklet/fr_CH/1.0.pdf" in result.output
    assert "Added voting_booklet/fr_CH/2.0.pdf" in result.output
    assert "Added voting_text/de_CH/1.0.pdf" in result.output
    assert "Added voting_text/de_CH/2.0.pdf" in result.output
    assert "Added voting_text/fr_CH/1.0.pdf" in result.output
    assert "Added voting_text/fr_CH/2.0.pdf" in result.output

    for number in (1, 2):
        vote = session.query(SwissVote).filter_by(id=number).one()
        for lang in ('de', 'fr'):
            vote.session_manager.current_locale = f'{lang}_CH'
            for name in (
                'federal_council_message',
                'parliamentary_debate',
                'realization',
                'resolution',
                'voting_booklet',
                'voting_text',
            ):
                assert f'{number}{name}{lang}' in getattr(vote, name).extract


def test_reindex(session_manager, temporary_directory, redis_url):

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    write_config(cfg_path, session_manager.dsn, temporary_directory, redis_url)

    result = run_command(cfg_path, 'govikon', ['add'])
    assert result.exit_code == 0
    assert "Instance was created successfully" in result.output

    result = run_command(cfg_path, 'govikon', ['reindex'])
    assert result.exit_code == 0

    # Add vote
    vote = SwissVote(
        id=1,
        bfs_number=Decimal(1),
        date=date(1990, 6, 2),
        decade=NumericRange(1990, 1999),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        votes_on_same_day=3,
        _legal_form=1,
    )

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_report()
    pdf.p("Abstimmungstext")
    pdf.generate()
    file.seek(0)

    attachment = SwissVoteFile(id=random_token())
    attachment.reference = as_fileintent(file, 'voting_text')
    vote.voting_text = attachment

    session_manager.ensure_schema_exists('onegov_swissvotes-govikon')
    session_manager.set_current_schema('onegov_swissvotes-govikon')
    session = session_manager.session()
    session.add(vote)
    session.flush()
    commit()

    result = run_command(cfg_path, 'govikon', ['reindex'])
    assert result.exit_code == 0
    assert "Reindexed vote 1.00" in result.output

    vote = session.query(SwissVote).one()
    assert "abstimmungstex" in vote.searchable_text_de_CH

    with open(vote.voting_text.reference.file._file_path, 'wb') as file:
        pdf = Pdf(file)
        pdf.init_report()
        pdf.p("Realisation")
        pdf.generate()

    vote = session.query(SwissVote).one()
    assert "abstimmungstex" in vote.searchable_text_de_CH

    result = run_command(cfg_path, 'govikon', ['reindex'])
    assert result.exit_code == 0
    assert "Reindexed vote 1.00" in result.output

    vote = session.query(SwissVote).one()
    assert "realisa" in vote.searchable_text_de_CH
