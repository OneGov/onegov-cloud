""" Provides commands related to the onegov.core Framework. Currently only
updates.

"""

import click

from morepath import setup
from onegov.server.core import Server
from onegov.server.config import Config
from onegov.core.orm import Base, SessionManager
from webtest import TestApp as Client
from uuid import uuid4


@click.group()
@click.option('--config', default='onegov.yml', help="The config file to use")
@click.option('--namespace',
              default='*',
              help=(
                  "The namespace to run this command on (see onegov.yml). "
                  "If no namespace is given, all namespaces are updated. "
              ))
@click.pass_context
def cli(ctx, config, namespace):
    ctx.obj = {
        'config': Config.from_yaml_file(config),
        'namespace': namespace
    }


@cli.command()
@click.pass_context
def upgrade(ctx):
    """ Upgrades all application instances of the given namespace(s). """

    ctx = ctx.obj

    update_path = '/' + uuid4().hex

    for appcfg in ctx['config'].applications:

        # filter out namespaces on demand
        if ctx['namespace'] != '*' and appcfg.namespace != ctx['namespace']:
            continue

        # have a custom update application so we can get a proper execution
        # context with a request and a session
        config = setup()

        class UpdateApplication(appcfg.application_class):
            testing_config = config

        @UpdateApplication.path(path=update_path)
        class Update(object):
            pass

        @UpdateApplication.view(model=Update)
        def run_update(self, request):
            print("Running upgrade for {}".format(request.app.application_id))

        config.commit()

        # get all applications by looking at the existing schemas
        mgr = SessionManager(appcfg.configuration['dsn'], base=Base)
        schemas = mgr.list_schemas(limit_to_namespace=appcfg.namespace)

        # run a custom server and send a fake request
        server = Server(Config({
            'applications': [
                {
                    'path': appcfg.path,
                    'application': UpdateApplication,
                    'namespace': appcfg.namespace
                }
            ]
        }), configure_morepath=False)

        # build the path to the update view and call it
        c = Client(server)

        for schema in schemas:
            if appcfg.is_static:
                root = appcfg.path
            else:
                root = appcfg.path.replace('*', schema.split('-')[1])

            c.get(root + update_path)
