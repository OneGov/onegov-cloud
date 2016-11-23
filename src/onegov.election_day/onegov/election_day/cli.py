""" Provides commands used to initialize election day websites. """

import click
import os

from onegov.core.cli import command_group, pass_group_context
from onegov.election_day.models import ArchivedResult
from onegov.election_day.sms_processor import SmsQueueProcessor


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
        local_session = app.session()
        assert local_session.info['schema'] == app.schema

        available = app.session_manager.list_schemas()

        if app.principal:
            for key in app.principal.fetch:
                schema = '{}-{}'.format(app.namespace, key)
                assert schema in available
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
                        local_session.add(new_item)

        click.echo("Results fetched successfully")

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
