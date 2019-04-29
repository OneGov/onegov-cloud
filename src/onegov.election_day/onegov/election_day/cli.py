""" Provides commands used to initialize election day websites. """

import click
import os

from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.election_day.models import ArchivedResult
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.utils.pdf_generator import PdfGenerator
from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from onegov.election_day.utils.svg_generator import SvgGenerator
from pathlib import Path


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

        lockfile = Path(os.path.join(
            app.configuration.get('lockfile_path', ''),
            '.lock-{}'.format(app.schema)
        ))

        try:
            lockfile.touch(exist_ok=False)
        except FileExistsError:
            return
        else:
            renderer = D3Renderer(app)
            SvgGenerator(app, renderer).create_svgs()
            PdfGenerator(app, renderer).create_pdfs()
        finally:
            lockfile.unlink()

    return generate
