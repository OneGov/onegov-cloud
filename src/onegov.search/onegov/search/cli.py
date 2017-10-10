""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context


cli = command_group()


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def reindex(group_context):
    """ Reindexes all objects in the elasticsearch database. """

    def run_reindex(request, app):
        if not hasattr(request.app, 'es_client'):
            return

        title = "Reindexing {}".format(request.app.application_id)
        print(click.style(title, underline=True))

        session = request.app.session()
        request.app.es_perform_reindex()

        @request.after
        def cleanup(response):
            session.invalidate()
            session.bind.dispose()

    return run_reindex
