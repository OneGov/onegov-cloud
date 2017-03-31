""" Provides commands used to initialize election day websites. """

import click
import os

from onegov.core.cli import command_group, pass_group_context
from onegov.election_day import log
from onegov.election_day.models import ArchivedResult
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.media_generator import MediaGenerator
from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from pathlib import Path
from raven import Client


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an election day instance with to the database. For example:

        onegov-election-day --select '/onegov_election_day/zg' add

    """

    def add_instance(request, app):
        app.cache.invalidate()
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


@cli.command()
@click.argument('username')
@click.argument('password')
@click.option('--sentry')
@click.option('--originator')
def send_sms(username, password, sentry, originator):
    """ Sends the SMS in the smsdir for a given instance. For example:

        onegov-election-day --select '/onegov_election_day/zg' send_sms
            'info@seantis.ch' 'top-secret'

    """
    def send(request, app):
        path = os.path.join(app.configuration['sms_directory'], app.schema)
        if os.path.exists(path):
            qp = SmsQueueProcessor(
                path,
                username,
                password,
                sentry,
                originator
            )
            qp.send_messages()

    return send


@cli.command('generate-media')
@click.option('--pdf/--no-pdf', default=True)
@click.option('--svg/--no-svg', default=True)
@click.option('--force/--no-force', default=False)
@click.option('--cleanup/--no-cleanup', default=True)
@click.option('--sentry')
def generate_media(pdf, svg, force, cleanup, sentry):
    """ Generates the PDF and/or SVGs for the selected instances

        onegov-election-day --select '/onegov_election_day/zg' generate-media

    """
    def generate(request, app):
        if not app.principal or not app.configuration.get('d3_renderer'):
            return

        if not pdf and not svg:
            return

        lockfile = Path(os.path.join(
            app.configuration.get('lockfile_path', ''),
            '.lock-{}'.format(app.schema)
        ))

        try:
            lockfile.touch(exist_ok=False)
        except OSError:
            pass
        else:
            try:
                client = Client(sentry) if sentry else None
                media_generator = MediaGenerator(app, force, cleanup)
                try:
                    if pdf:
                        media_generator.create_pdfs()
                    if svg:
                        media_generator.create_svgs()
                except:
                    if client:
                        client.captureException()
                    else:
                        log.error(
                            "Error while generating media",
                            exc_info=True
                        )
            finally:
                lockfile.unlink()

    return generate
