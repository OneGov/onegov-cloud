""" Provides commands used to initialize election day websites. """
from __future__ import annotations

import click
import os

from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.sms_processor import SmsQueueProcessor
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Subscriber
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.archive_generator import ArchiveGenerator
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.utils.pdf_generator import PdfGenerator
from onegov.election_day.utils.svg_generator import SvgGenerator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.cli.core import GroupContext
    from onegov.election_day.app import ElectionDayApp
    from onegov.election_day.request import ElectionDayRequest
    from typing import TypeAlias

    Processor: TypeAlias = Callable[[ElectionDayRequest, ElectionDayApp], None]


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context: GroupContext) -> Processor:
    """ Adds an election day instance with to the database. For example:

    .. code-block:: bash

        onegov-election-day --select '/onegov_election_day/zg' add

    """

    def add_instance(
        request: ElectionDayRequest,
        app: ElectionDayApp
    ) -> None:
        app.cache.flush()
        if not app.principal:
            click.secho('principal.yml not found', fg='yellow')

        click.echo('Instance was created successfully')

    return add_instance


@cli.command()
@pass_group_context
def fetch(group_context: GroupContext) -> Processor:
    """ Fetches the results from other instances as defined in the
    principal.yml. Only fetches results from the same namespace.

    .. code-block:: bash

        onegov-election-day --select '/onegov_election_day/zg' fetch

    """

    def fetch_results(
        request: ElectionDayRequest,
        app: ElectionDayApp
    ) -> None:
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


# TODO: Get rid of this command, there is now an equivalent command in
#       core as well as an option to run a daemon
@cli.command('send-sms')
@click.argument('username')
@click.argument('password')
@click.option('--originator')
@pass_group_context
def send_sms(
    group_context: GroupContext,
    username: str,
    password: str,
    originator: str | None
) -> Processor:
    r""" Sends the SMS in the smsdir for a given instance. For example:

    .. code-block:: bash

        onegov-election-day --select '/onegov_election_day/zg' \
            send_sms 'info@seantis.ch' 'top-secret'

    """

    def send(
        request: ElectionDayRequest,
        app: ElectionDayApp
    ) -> None:
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
def generate_media() -> Processor:
    """ Generates the PDF and/or SVGs for the selected instances. For example:

    .. code-block:: bash

        onegov-election-day --select '/onegov_election_day/zg' generate-media

    """

    def generate(request: ElectionDayRequest, app: ElectionDayApp) -> None:
        if not app.principal or not app.configuration.get('d3_renderer'):
            return

        click.secho(f'Generating media for {app.schema}', fg='yellow')
        renderer = D3Renderer(app)

        created, purged = SvgGenerator(app, renderer).create_svgs()
        click.secho(f'Generated {created} SVGs, purged {purged}', fg='green')

        created, purged = PdfGenerator(app, request, renderer).create_pdfs()
        click.secho(f'Generated {created} PDFs, purged {purged}', fg='green')

    return generate


@cli.command('generate-archive')
def generate_archive() -> Processor:
    """ Generates a zipped file of the entire archive.

    .. code-block:: bash
        onegov-election-day --select '/onegov_election_day/zg' generate-archive
    """
    def generate(request: ElectionDayRequest, app: ElectionDayApp) -> None:

        click.secho('Starting archive.zip generation.')

        archive_generator = ArchiveGenerator(app)
        archive_zip = archive_generator.generate_archive()
        if not archive_zip:
            abort('generate_archive returned None.')

        archive_filesize = archive_generator.archive_dir.getinfo(
            archive_zip, namespaces=['details']).size

        if archive_filesize == 0:
            click.secho('Generated archive is empty', fg='red')
        else:
            click.secho('Archive generated successfully:', fg='green')
        absolute_path = archive_generator.archive_system_path
        if absolute_path:
            click.secho(f'file://{absolute_path}')

    return generate


@cli.command('update-archived-results')
@click.option('--host', default='localhost:8080')
@click.option('--scheme', default='http')
def update_archived_results(host: str, scheme: str) -> Processor:
    """ Update the archive results, e.g. after a database transfer. """

    def generate(request: ElectionDayRequest, app: ElectionDayApp) -> None:
        if (
            app.principal
            and app.principal.official_host is None
            or host == 'localhost:8080'
        ):
            click.secho(
                'Official host is not set! Do not run this command on '
                'staging. Uploading results later  may create '
                'duplicate archived result entries.',
                fg='red',
            )
            click.secho(
                'Use `/update-results` view or `update archive` '
                'menu, both available for admins only on the UI',
                fg='yellow',
            )
            return

        click.secho(f'Updating {app.schema}', fg='yellow')
        request.host = host
        request.environ['wsgi.url_scheme'] = scheme
        archive = ArchivedResultCollection(request.session)
        archive.update_all(request)

    return generate


@cli.command('migrate-subscribers')
def migrate_subscribers() -> Processor:
    def migrate(request: ElectionDayRequest, app: ElectionDayApp) -> None:
        if not app.principal or not app.principal.segmented_notifications:
            return

        click.secho(f'Migrating {app.schema}', fg='yellow')

        session = request.app.session()
        subscribers = session.query(Subscriber).filter_by(domain=None)
        count = 0
        for subscriber in subscribers:
            subscriber.domain = 'canton'
            count += 1
        click.echo(f'Migrated {count} subscribers')

    return migrate
