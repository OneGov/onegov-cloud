""" Provides commands related to the onegov.core Framework. Currently only
updates.

"""

import click
import email
import mailbox
import os
import platform
import subprocess
import sys

from fnmatch import fnmatch
from mailthon.middleware import TLS, Auth
from onegov.core.mail import Postman
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import UpgradeRunner, get_tasks, get_upgrade_modules
from onegov.core.utils import scan_morepath_modules
from onegov.server.config import Config
from onegov.server.core import Server
from smtplib import SMTPRecipientsRefused
from uuid import uuid4
from webtest import TestApp as Client


# missing selector
MISSING = object()


class GroupContext(object):
    """ Provides access to application configs for group commands.

    """

    def __init__(self, selector, config):
        if isinstance(config, dict):
            self.config = Config(config)
        else:
            self.config = Config.from_yaml_file(config)
        self.selector = selector

    def unbound_session_manager(self, dsn):
        """ Returns a session manager *not yet bound to a schema!*. """

        return SessionManager(dsn=dsn, base=Base)

    def available_schemas(self, appcfg):
        mgr = self.unbound_session_manager(appcfg.configuration['dsn'])
        return mgr.list_schemas(limit_to_namespace=appcfg.namespace)

    @property
    def appcfgs(self):
        """ Returns the matching appconfigs.

        Since there's only one appconfig per namespace, we ignore the path
        part of the selector and only focus on the namespace:

            /namespace/application_id

        """
        namespace = self.selector.lstrip('/').split('/')[0]

        for appcfg in self.config.applications:
            if namespace != '*' and namespace != appcfg.namespace:
                continue

            yield appcfg

    @property
    def available_selectors(self):
        selectors = list(self.all_wildcard_paths)
        selectors.extend(self.all_paths)

        return sorted(selectors)

    @property
    def all_wildcard_paths(self):
        for appcfg in self.config.applications:
            if appcfg.path.endswith('*'):
                yield appcfg.path

    @property
    def all_paths(self):
        for appcfg in self.config.applications:
            if not appcfg.path.endswith('*'):
                yield appcfg.path
            else:
                for schema in self.available_schemas(appcfg):
                    yield '/' + schema.replace('-', '/')

    @property
    def matching_paths(self):
        assert self.selector is not MISSING

        for path in self.all_paths:
            if fnmatch(path, self.selector):
                yield path


#: Decorator to acquire the group context on a command:
#:
#:     @cli.command()
#:     @pass_group_context()
#:     def my_command(group_context):
#:         pass
#:
pass_group_context = click.make_pass_decorator(GroupContext, ensure=True)


def command_group():
    """ Generates a click command group for individual modules.

    Each individual module may have its own command group from which to run
    commands to. Read `<http://click.pocoo.org/6/commands/>`_ to learn more
    about command groups.

    The returned command group will provide the individual commands with
    an optional list of applications to operate on and it allows commands
    to return a callback function which will be invoked with the app config
    (if available), an application instance and a request.

    That is to say, the command group automates setting up a proper request
    context.

    """

    @click.group(invoke_without_command=True)
    @click.argument('selector', default=MISSING)
    @click.option(
        '--config',
        default='onegov.yml',
        help="The onegov config file")
    def command_group(selector, config):
        context = click.get_current_context()
        context.obj = group_context = GroupContext(selector, config)

        click.secho("Given selector: {}".format(selector), fg='green')

        # no selector was provided, print available
        if selector is MISSING:
            click.secho("Available selectors:")

            for selector in context.obj.available_selectors:
                click.secho(" - {}".format(selector))

            abort("No selector provided, aborting.")

        matching_paths = tuple(context.obj.matching_paths)

        # no subcommand was provided, print selector matches
        if context.invoked_subcommand is None:
            click.secho("Paths matching the selector:")

            for match in matching_paths:
                click.secho(" - {}".format(match))

            abort("No subcommand provided, aborting.")

        subcommand = context.command.commands[context.invoked_subcommand]
        settings = subcommand.context_settings

        group_context.creates_path = settings.pop('creates_path', False)

        # the subcommand requires a matching selector but we didn't get one
        if not group_context.creates_path and not matching_paths:
            click.secho("Available selectors:")

            for selector in context.obj.available_selectors:
                click.secho(" - {}".format(selector))

            abort("Selector doesn't match any paths, aborting.")

        # the subcommand requires a single match, but we have more than that
        if group_context.creates_path and len(matching_paths) > 1:
            click.secho("Paths matching the selector:")

            for match in matching_paths:
                click.secho(" - {}".format(match))

            abort("The selector must match a single path, aborting.")

        if group_context.creates_path:
            if matching_paths:
                abort("This selector may not reference an existing path")

            if len(selector.lstrip('/').split('/')) != 2:
                abort("This selector must reference a full path")

            if '*' in selector:
                abort("This selector may not contain a wildcard")

    @command_group.resultcallback()
    def process_results(processor, selector, config):

        group_context = click.get_current_context().obj

        for appcfg in group_context.appcfgs:
            scan_morepath_modules(appcfg.application_class)

        for appcfg in group_context.appcfgs:

            view_path = uuid4().hex

            class CliApplication(appcfg.application_class):

                def is_allowed_application_id(self, application_id):

                    if group_context.creates_path:
                        return True

                    return super().is_allowed_application_id(application_id)

            @CliApplication.path(path=view_path)
            class Model(object):
                pass

            @CliApplication.view(model=Model)
            def run_command(self, request):
                processor(request, request.app)

            CliApplication.commit()

            # run a custom server and send a fake request
            server = Server(Config({
                'applications': [
                    {
                        'path': appcfg.path,
                        'application': CliApplication,
                        'namespace': appcfg.namespace,
                        'configuration': appcfg.configuration
                    }
                ]
            }), configure_morepath=False)

            client = Client(server)

            # call the view for all paths
            paths = list(group_context.matching_paths)

            if group_context.creates_path:
                paths.append(group_context.selector.rstrip('/'))

            for path in paths:
                client.get(path + '/' + view_path)

    return command_group


def abort(msg):
    """ Prints the given error message and aborts the program with a return
    code of 1.

    """
    click.secho(msg, fg='red')

    sys.exit(1)


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
@click.option('--limit', default=25,
              help="Max number of mails to send before exiting")
@click.pass_context
def sendmail(ctx, hostname, port, force_tls, username, password, limit):
    """ Iterates over all applications and processes the maildir for each
    application that uses maildir e-mail delivery.

    """
    context = ctx.obj
    success = True

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

            for n, filename in enumerate(maildir.keys(), start=1):

                if limit and n > limit:
                    break

                msg_str = maildir.get_file(filename).read()
                msg_str = msg_str.decode('utf-8')

                msg = email.message_from_string(msg_str)

                try:
                    connection.sendmail(msg['From'], msg['To'], msg_str)
                    status, message = connection.noop()
                except SMTPRecipientsRefused as e:
                    success = False
                    print("Could not send e-mail: {}".format(e.recipients))
                    maildir.remove(filename)
                else:
                    if status == 250:
                        maildir.remove(filename)

        if not success:
            sys.exit(1)


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
                    "--no-owner --no-privileges --clean {}".format(
                        remote_db
                    )
                ),
            ])

            with open('dump.sql', 'w') as f:
                # add cascade to all drop schema lines
                # http://www.postgresql.org/message-id/50EC9574.9060500
                for line in database_dump.splitlines():
                    line = line.decode('utf-8')

                    if line.startswith('DROP SCHEMA'):
                        if 'CASCADE' not in line:
                            if 'DROP SCHEMA extensions' not in line:
                                line = line.replace(';', ' CASCADE;')

                    f.write(line + os.linesep)

            try:
                if platform.system() == 'Darwin':
                    subprocess.check_output([
                        "cat dump.sql | psql {}".format(local_db)
                    ], stderr=subprocess.STDOUT, shell=True)
                elif platform.system() == 'Linux':
                    subprocess.check_output([
                        (
                            "cat dump.sql "
                            "| sudo -u postgres psql -d {}".format(
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

        class UpdateApplication(appcfg.application_class):
            pass

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

        scan_morepath_modules(appcfg.application_class)
        UpdateApplication.commit()

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
            print(click.style("* " + str(task.task_name), fg='green'))

        def on_fail(task):
            print(click.style("* " + str(task.task_name), fg='red'))

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
