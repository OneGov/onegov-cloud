""" Provides commands used to initialize election day websites. """
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ListPanachageResult
from onegov.ballot import PartyPanachageResult
from onegov.ballot import Vote
from onegov.ballot.models.election.panachage_result import PanachageResult
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.archive_generator import ArchiveGenerator
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.utils.pdf_generator import PdfGenerator
from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from onegov.election_day.utils.svg_generator import SvgGenerator
from uuid import UUID
import click
import os

cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an election day instance with to the database. For example:

        onegov-election-day --select '/onegov_election_day/zg' add

    """

    def add_instance(request, app):
        app.cache.flush()
        if not app.principal:
            click.secho("principal.yml not found", fg='yellow')

        click.echo("Instance was created successfully")

    return add_instance


@cli.command()
@pass_group_context
def fetch(group_context):
    """ Fetches the results from other instances as defined in the
        principal.yml. Only fetches results from the same namespace.

        onegov-election-day --select '/onegov_election_day/zg' fetch

    """

    def fetch_results(request, app):
        if not app.principal:
            return

        local_session = app.session()
        assert local_session.info['schema'] == app.schema

        for key in app.principal.fetch:
            schema = '{}-{}'.format(app.namespace, key)
            assert schema in app.session_manager.list_schemas()
            app.session_manager.set_current_schema(schema)
            remote_session = app.session_manager.session()
            assert remote_session.info['schema'] == schema

            items = local_session.query(ArchivedResult)
            items = items.filter_by(schema=schema)
            for item in items:
                local_session.delete(item)

            for domain in app.principal.fetch[key]:
                items = remote_session.query(ArchivedResult)
                items = items.filter_by(schema=schema, domain=domain)
                for item in items:
                    new_item = ArchivedResult()
                    new_item.copy_from(item)
                    add_local_results(
                        item, new_item, app.principal, remote_session
                    )
                    local_session.add(new_item)

    return fetch_results


@cli.command('send-sms')
@click.argument('username')
@click.argument('password')
@click.option('--originator')
@pass_group_context
def send_sms(group_context, username, password, originator):
    """ Sends the SMS in the smsdir for a given instance. For example:

        onegov-election-day --select '/onegov_election_day/zg' send_sms
            'info@seantis.ch' 'top-secret'

    """

    def send(request, app):
        if 'sms_directory' in app.configuration:
            path = os.path.join(app.configuration['sms_directory'], app.schema)
            if os.path.exists(path):
                qp = SmsQueueProcessor(
                    path,
                    username,
                    password,
                    originator
                )
                qp.send_messages()

    return send


@cli.command('generate-media')
def generate_media():
    """ Generates the PDF and/or SVGs for the selected instances. For example:

        onegov-election-day --select '/onegov_election_day/zg' generate-media

    """

    def generate(request, app):
        if not app.principal or not app.configuration.get('d3_renderer'):
            return

        click.secho(f'Generating media for {app.schema}', fg='yellow')
        renderer = D3Renderer(app)

        created, purged = SvgGenerator(app, renderer).create_svgs()
        click.secho(f'Generated {created} SVGs, purged {purged}', fg='green')

        created, purged = PdfGenerator(app, renderer).create_pdfs()
        click.secho(f'Generated {created} PDFs, purged {purged}', fg='green')

    return generate


@cli.command('generate-archive')
def generate_archive():
    """ Generates a zipped file of the entire archive.
        onegov-election-day --select '/onegov_election_day/zg' generate-archive
    """
    def generate(request, app):

        click.secho('Starting archive.zip generation.')

        archive_generator = ArchiveGenerator(app)
        archive_zip = archive_generator.generate_archive()
        if not archive_zip:
            click.secho("generate_archive returned None.", fg='red')
        archive_filesize = archive_generator.archive_dir.getinfo(
            archive_zip, namespaces=['details']).size

        if archive_filesize == 0:
            click.secho("Generated archive is empty", fg='red')
        else:
            click.secho("Archive generated successfully:", fg='green')
        absolute_path = archive_generator.archive_system_path
        if absolute_path:
            click.secho(f"file://{absolute_path}")

    return generate


@cli.command('update-archived-results')
@click.option('--host', default='localhost:8080')
@click.option('--scheme', default='http')
def update_archived_results(host, scheme):
    """ Update the archive results, e.g. after a database transfer. """

    def generate(request, app):
        click.secho(f'Updating {app.schema}', fg='yellow')
        request.host = host
        request.environ['wsgi.url_scheme'] = scheme
        archive = ArchivedResultCollection(request.session)
        archive.update_all(request)

    return generate


@cli.command('update-last-result-change')
def update_last_result_change():
    """ Update the last result changes. """

    def update(request, app):
        click.secho(f'Updating {app.schema}', fg='yellow')

        count = 0

        session = request.app.session()
        for item in session.query(Election):
            result = item.results.first()
            if result:
                item.last_result_change = result.last_change
                count += 1

        for item in session.query(ElectionCompound):
            result = [x.last_result_change for x in item.elections]
            result = [x for x in result if x]
            if result:
                item.last_result_change = max(result)
                count += 1

        for item in session.query(Vote):
            result = [x.results.first() for x in item.ballots]
            result = [x.last_change if x else None for x in result]
            result = [x for x in result if x]
            if result:
                item.last_result_change = max(result)
                count += 1

        click.secho(f'Updated {count} items', fg='green')

    return update


@cli.command('migrate-panachage-results')
@click.option('--clear', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, default=False)
def migrate_panachage_results(clear, dry_run, verbose):

    def migrate(request, app):
        click.secho(f'Migrating {app.schema}', fg='yellow')

        migrated = 0
        ignored = 0

        if clear:
            # todo:
            pass

        session = request.app.session()
        for item in session.query(PanachageResult):
            type_ = 'list'
            try:
                UUID(item.target)
            except ValueError:
                type_ = 'party'

            try:
                if type_ == 'list':
                    # list
                    assert item.votes >= 0
                    assert not item.election_id
                    assert not item.election_compound_id
                    assert item.source  # blank list is '999'
                    assert item.target
                    if not dry_run:
                        session.add(
                            ListPanachageResult(
                                votes=item.votes,
                                source=item.source,
                                target=UUID(item.target)
                            )
                        )
                else:
                    # party
                    assert item.votes >= 0
                    assert item.election_id or item.election_compound_id
                    assert item.source != '999'  # blank list is ''
                    assert item.target
                    if not dry_run:
                        session.add(
                            PartyPanachageResult(
                                votes=item.votes,
                                source=item.source,
                                target=item.target,
                                election_id=item.election_id,
                                election_compound_id=item.election_compound_id
                            )
                        )
            except AssertionError:
                ignored += 1
                if verbose:
                    click.secho(
                        f'Ignoring {type_} '
                        f'{item.source}->{item.target}: {item.votes} '
                        f'[e: {item.election_id}] '
                        f'[c:{item.election_compound_id}]',
                        fg='red'
                    )

        if dry_run:
            click.secho(
                f'would migrate {migrated}, ignore {ignored}',
                fg='green'
            )
        else:
            click.secho(
                f'{migrated} migrated, {ignored} ignored',
                fg='green'
            )

    return migrate
