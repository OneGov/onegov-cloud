""" Provides commands used to initialize election day websites. """

import click
import os

from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import DataSource
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.utils.pdf_generator import PdfGenerator
from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from onegov.election_day.utils.svg_generator import SvgGenerator


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

        renderer = D3Renderer(app)
        SvgGenerator(app, renderer).create_svgs()
        PdfGenerator(app, renderer).create_pdfs()

    return generate


@cli.command('delete-associated')
@click.option('--wabsti-token')
@click.option('--delete-compound', help='Delete the compound if it exists')
def delete_associated(wabsti_token, delete_compound):

    def delete(request, app):
        query = request.session.query(DataSource)
        query = query.filter(DataSource.token == wabsti_token)
        data_source = query.one()

        compound = None
        session = request.session

        for item in data_source.items:
            election = item.item
            click.secho(f'Deleting election {election.shortcode}')
            if not compound and election.compound:
                compound = election.compound
            election.clear_results()
            session.delete(item)
            session.delete(election)

        if delete_compound and compound:
            click.secho(f'Deleting {compound.title}')
            session.delete(compound)

    return delete


@cli.command('update-last-result-change')
def update_last_result_change():

    def update(request, app):
        session = request.app.session()
        for item in session.query(Election):
            result = item.results.first()
            if result:
                item.last_result_change = result.last_change

        for item in session.query(ElectionCompound):
            result = [x.last_result_change for x in item.elections]
            result = [x for x in result if x]
            if result:
                item.last_result_change = max(result)

        for item in session.query(Vote):
            result = [x.results.first() for x in item.ballots]
            result = [x.last_change if x else None for x in result]
            result = [x for x in result if x]
            if result:
                item.last_result_change = max(result)

    return update
