""" Provides commands related to the onegov.search. """

import click

from onegov.core.cli import command_group, pass_group_context
from onegov.search.utils import searchable_sqlalchemy_models


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

        app = request.app
        session = app.session()
        es_client = app.es_client

        app.es_indexer.ixmgr.created_indices = set()

        # delete all existing indices for this town
        ixs = app.es_indexer.ixmgr.get_managed_indices_wildcard(app.schema)
        es_client.indices.delete(ixs)

        for base in app.session_manager.bases:
            for model in searchable_sqlalchemy_models(base):
                for obj in session.query(model).all():
                    app.es_orm_events.index(app.schema, obj)
                    app.es_indexer.process()

        @request.after
        def cleanup(response):
            session.invalidate()
            session.bind.dispose()

    return run_reindex
