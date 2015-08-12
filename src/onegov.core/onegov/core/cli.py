# -*- coding: utf-8 -*-
""" Provides commands related to the onegov.core Framework. Currently only
updates.

"""

import click
import email
import mailbox
import os
import platform
import subprocess

from mailthon.middleware import TLS, Auth
from morepath import setup
from onegov.core.compat import text_type, PY3
from onegov.core.mail import Postman
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import UpgradeRunner, get_tasks, get_upgrade_modules
from onegov.server.config import Config
from onegov.server.core import Server
from uuid import uuid4
from webtest import TestApp as Client


class Context(object):

    def __init__(self, config, namespace):
        self.config = config
        self.namespace = namespace

    @property
    def appconfigs(self):
        for appcfg in self.config.applications:
            if self.namespace != '*' and self.namespace != appcfg.namespace:
                continue

            yield appcfg


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
    ctx.obj = Context(Config.from_yaml_file(config), namespace)


@cli.command()
@click.option('--hostname', help="The smtp host")
@click.option('--port', help="The smtp port")
@click.option('--force-tls', default=False, is_flag=True,
              help="Force a TLS connection")
@click.option('--username', help="The username to authenticate", default=None)
@click.option('--password', help="The password to authenticate", default=None)
@click.pass_context
def sendmail(ctx, hostname, port, force_tls, username, password):
    """ Iterates over all applications and processes the maildir for each
    application that uses maildir e-mail delivery.

    """
    context = ctx.obj

    for appcfg in context.appconfigs:

        if not appcfg.configuration.get('mail_use_directory'):
            continue

        maildir = mailbox.Maildir(
            appcfg.configuration.get('mail_directory'), create=False)

        if not len(maildir):
            return

        middlewares = []

        if force_tls:
            middlewares.append(TLS(force=True))

        if username:
            middlewares.append(Auth(username, password))

        postman = Postman(hostname, port, middlewares)

        with postman.connection() as connection:

            for filename in maildir.keys():
                msg_str = maildir.get_file(filename).read()

                if PY3:
                    msg_str = msg_str.decode('utf-8')

                msg = email.message_from_string(msg_str)

                connection.sendmail(msg['From'], msg['To'], msg_str)
                status, message = connection.noop()

                if status == 250:
                    maildir.remove(filename)


@cli.command()
@click.argument('server')
@click.argument('remote-config')
@click.option('--confirm/--no-confirm', default=True,
              help="Ask for confirmation (disabling this is dangerous!)")
@click.option('--no-filestorage', default=False, is_flag=True,
              help="Do not transfer the files")
@click.option('--no-database', default=False, is_flag=True,
              help="Do not transfer the database")
@click.pass_context
def transfer(ctx, server, remote_config, confirm, no_filestorage, no_database):
    """ Transfers the database and all files from a server running a
    onegov-cloud application and installs them locally, overwriting the
    local data!

    This command expects to have access to the remote server via ssh
    (no password) and to be run sudo without password. If this is too scary
    for you, feel free to write something saner.

    Only namespaces which are present locally and remotely are considered.

    So if you have a 'cities' namespace locally and a 'towns' namespace on
    the remote, nothing will happen.

    WARNING: This may delete local content!

    """

    context = ctx.obj

    if confirm:
        click.confirm(
            "Do you really want override all your local data?",
            default=False, abort=True
        )

    print("Parsing the remote application configuration")

    remote_dir = os.path.dirname(remote_config)
    remote_config = Config.from_yaml_string(
        subprocess.check_output([
            "ssh", server, "-C", "sudo cat '{}'".format(remote_config)
        ])
    )

    remote_applications = {a.namespace: a for a in remote_config.applications}

    # storages may be shared between applications, so we need to keep track
    fetched = set()

    # filter out namespaces on demand
    for appcfg in context.appconfigs:

        if appcfg.configuration.get('disable_transfer'):
            print("Skipping {}, transfer disabled".format(appcfg.namespace))
            continue

        if appcfg.namespace not in remote_applications:
            print("Skipping {}, not found on remote".format(appcfg.namespace))
            continue

        remotecfg = remote_applications[appcfg.namespace]

        if not no_filestorage:
            if remotecfg.configuration.get('filestorage') == 'fs.osfs.OSFS':
                assert appcfg.configuration.get('filestorage')\
                    == 'fs.osfs.OSFS'

                print("Fetching remote filestorage")

                local_fs = appcfg.configuration['filestorage_options']
                remote_fs = remotecfg.configuration['filestorage_options']

                remote_storage = os.path.join(
                    remote_dir, remote_fs['root_path'])
                local_storage = os.path.join('.', local_fs['root_path'])

                if ':'.join((remote_storage, local_storage)) in fetched:
                    continue

                tar_filename = '/tmp/{}.tar.gz'.format(uuid4().hex)

                subprocess.check_output([
                    'ssh', server, '-C', "sudo tar czvf '{}' -C '{}' .".format(
                        tar_filename, remote_storage
                    )
                ])

                subprocess.check_output([
                    'scp',
                    '{}:{}'.format(server, tar_filename),
                    '{}/transfer.tar.gz'.format(local_storage)
                ])

                subprocess.check_output([
                    'tar', 'xzvf', '{}/transfer.tar.gz'.format(local_storage),
                    '-C', local_storage
                ])

                subprocess.check_output([
                    'ssh', server, '-C', "sudo rm '{}'".format(tar_filename)
                ])

                subprocess.check_output([
                    'rm', '{}/transfer.tar.gz'.format(local_storage)
                ])

                fetched.add(':'.join((remote_storage, local_storage)))

        if 'dsn' in remotecfg.configuration:
            assert 'dsn' in appcfg.configuration

            print("Fetching remote database")

            local_db = appcfg.configuration['dsn'].split('/')[-1]
            remote_db = remotecfg.configuration['dsn'].split('/')[-1]
            database_dump = subprocess.check_output([
                'ssh', server, '-C',
                (
                    "sudo -u postgres pg_dump "
                    "--format=c --no-owner --no-privileges --clean {}".format(
                        remote_db
                    )
                ),
            ])

            with open('dump.sql', 'wb') as f:
                f.write(database_dump)

            try:
                if platform.system() == 'Darwin':
                    subprocess.check_output([
                        "cat dump.sql | pg_restore -d {}".format(local_db)
                    ], stderr=subprocess.STDOUT, shell=True)
                elif platform.system() == 'Linux':
                    subprocess.check_output([
                        (
                            "cat dump.sql "
                            "| sudo -u postgres pg_restore -d {}".format(
                                local_db
                            )
                        )
                    ], stderr=subprocess.STDOUT, shell=True)
                else:
                    raise NotImplementedError
            except subprocess.CalledProcessError as e:
                lines = e.output.decode('utf-8').rstrip('\n').split('\n')

                if lines[-1].startswith('WARNING: errors ignored on restore:'):
                    pass
                else:
                    raise
            finally:
                subprocess.check_output(['rm', 'dump.sql'])


@cli.command()
@click.option('--dry-run', default=False, is_flag=True,
              help="Do not write any changes into the database.")
@click.pass_context
def upgrade(ctx, dry_run):
    """ Upgrades all application instances of the given namespace(s). """

    context = ctx.obj

    update_path = '/' + uuid4().hex

    modules = list(get_upgrade_modules())
    tasks = get_tasks()

    for appcfg in context.appconfigs:

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
