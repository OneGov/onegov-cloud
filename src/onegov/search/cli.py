""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from sedate import utcnow

cli = command_group()


@cli.command(context_settings={'default_selector': '*'})
@click.option('--fail', is_flag=True, default=False, help='Fail on errors')
@pass_group_context
def reindex(group_context, fail):
    """ Reindexes all objects in the postgresql database. """

    def run_reindex(request, app):
        """
        Looping over all models in project deleting all full text search (
        fts) indexes in postgresql and re-creating them

        :param request: request
        :param app: application context
        """
        session = request.session

        title = f"Reindexing {request.app.application_id}"
        print(click.style(title, underline=True))

        start = utcnow()

        app.psql_perform_reindex(session)
        request.app.es_perform_reindex(fail)  # TODO: remove

        print(f"took {utcnow() - start}")

    return run_reindex
