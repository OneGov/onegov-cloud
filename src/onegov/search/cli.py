""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from sedate import utcnow


cli = command_group()


@cli.command(context_settings={'default_selector': '*'})
@click.option('--fail', is_flag=True, default=False, help='Fail on errors')
@pass_group_context
def reindex(group_context, fail):
    """ Reindexes all objects in the elasticsearch database. """

    def run_reindex(request, app):
        if not hasattr(request.app, 'es_client'):
            return

        title = f"Reindexing {request.app.application_id}"
        print(click.style(title, underline=True))

        start = utcnow()
        request.app.es_perform_reindex(fail)

        print(f"took {utcnow() - start}")

    return run_reindex


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def index_status(group_context):
    """ Prints the status of the index. """

    def run_index_status(request, app):
        title = f"Index status of {request.app.application_id}"
        print(click.style(title, underline=True))

        request.app.psql_index_status()

    return run_index_status
