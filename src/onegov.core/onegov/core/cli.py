# -*- coding: utf-8 -*-
""" Provides commands related to the onegov.core Framework. Currently only
updates.

"""

import click

from morepath import setup
from onegov.core.compat import text_type
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import UpgradeRunner, get_tasks, get_upgrade_modules
from onegov.server.config import Config
from onegov.server.core import Server
from uuid import uuid4
from webtest import TestApp as Client


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
@click.option('--dry-run', default=False, is_flag=True,
              help="Do not write any changes into the database.")
@click.pass_context
def upgrade(ctx, dry_run):
    """ Upgrades all application instances of the given namespace(s). """

    ctx = ctx.obj

    update_path = '/' + uuid4().hex

    modules = list(get_upgrade_modules())
    tasks = get_tasks()

    for appcfg in ctx['config'].applications:

        # filter out namespaces on demand
        if ctx['namespace'] != '*' and appcfg.namespace != ctx['namespace']:
            continue

        # have a custom update application so we can get a proper execution
        # context with a request and a session
        config = setup()

        class UpdateApplication(appcfg.application_class):
            testing_config = config

        @UpdateApplication.path(model=UpgradeRunner, path=update_path)
        def get_upgrade_runner():
            return upgrade_runner

        @UpdateApplication.view(model=UpgradeRunner)
        def run_upgrade(self, request):
            title = "Running upgrade for {}".format(request.app.application_id)
            print(click.style(title, underline=True))

            executed_tasks = self.run_upgrade(request)

            if executed_tasks:
                print("executed {} upgrade tasks".format(executed_tasks))
            else:
                print("no pending upgrade tasks found")

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
                    'namespace': appcfg.namespace,
                    'configuration': appcfg.configuration
                }
            ]
        }), configure_morepath=False)

        # build the path to the update view and call it
        c = Client(server)

        def on_success(task):
            print(click.style("* " + text_type(task.task_name), fg='green'))

        def on_fail(task):
            print(click.style("* " + text_type(task.task_name), fg='red'))

        for schema in schemas:
            # we *need* a new upgrade runner for each schema
            upgrade_runner = UpgradeRunner(
                modules=modules,
                tasks=tasks,
                commit=not dry_run,
                on_task_success=on_success,
                on_task_fail=on_fail
            )

            if appcfg.is_static:
                root = appcfg.path
            else:
                root = appcfg.path.replace('*', schema.split('-')[1])

            c.get(root + update_path)
