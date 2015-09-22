""" Provides commands related to the onegov.search. """

import click

from morepath import setup
from onegov.core.cli import Context
from onegov.core.orm import Base, SessionManager
from onegov.search.utils import searchable_sqlalchemy_models
from onegov.server.config import Config
from onegov.server.core import Server
from uuid import uuid4
from webtest import TestApp as Client


@click.group()
@click.option('--config',
              default='onegov.yml',
              help="The config file to use (default is onegov.yml)")
@click.option('--namespace',
              default='*',
              help=(
                  "The namespace to run this command on (see onegov.yml). "
                  "If no namespace is given, all namespaces are updated. "
              ))
@click.pass_context
def cli(ctx, config, namespace):
    ctx.obj = Context(Config.from_yaml_file(config), namespace)


@cli.command()
@click.pass_context
def reindex(ctx):
    """ Reindexes all objects in the elasticsearch database. """
    context = ctx.obj
    reindex_path = '/' + uuid4().hex

    for appcfg in context.appconfigs:

        # have a custom update application so we can get a proper execution
        # context with a request and a session
        config = setup()

        class ReindexApplication(appcfg.application_class):
            testing_config = config

        @ReindexApplication.path(path=reindex_path)
        class Reindex(object):
            pass

        @ReindexApplication.view(model=Reindex)
        def run_upgrade(self, request):
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

        config.commit()

        # get all applications by looking at the existing schemas
        mgr = SessionManager(appcfg.configuration['dsn'], base=Base)
        schemas = mgr.list_schemas(limit_to_namespace=appcfg.namespace)

        # run a custom server and send a fake request
        server = Server(Config({
            'applications': [
                {
                    'path': appcfg.path,
                    'application': ReindexApplication,
                    'namespace': appcfg.namespace,
                    'configuration': appcfg.configuration
                }
            ]
        }), configure_morepath=True)

        # build the path to the update view and call it
        c = Client(server)

        for schema in schemas:
            if appcfg.is_static:
                root = appcfg.path
            else:
                root = appcfg.path.replace('*', schema.split('-')[1])

            c.get(root + reindex_path)
