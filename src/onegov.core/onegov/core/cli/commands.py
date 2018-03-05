import click
import email
import mailbox
import os
import platform
import subprocess
import sys

from cached_property import cached_property
from mailthon.middleware import TLS, Auth
from onegov.core.cli.core import command_group, pass_group_context
from onegov.core.mail import Postman
from onegov.core.upgrade import get_tasks
from onegov.core.upgrade import get_upgrade_modules
from onegov.core.upgrade import RawUpgradeRunner
from onegov.core.upgrade import UpgradeRunner
from onegov.server.config import Config
from smtplib import SMTPRecipientsRefused
from uuid import uuid4


#: onegov.core's own command group
cli = command_group()


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@click.option('--hostname', help="The smtp host")
@click.option('--port', help="The smtp port")
@click.option('--force-tls', default=False, is_flag=True,
              help="Force a TLS connection")
@click.option('--username', help="The username to authenticate", default=None)
@click.option('--password', help="The password to authenticate", default=None)
@click.option('--limit', default=25,
              help="Max number of mails to send before exiting")
@click.option('--category', help="Only send e-mails of the given category",
              default=None)
@pass_group_context
def sendmail(group_context,
             hostname, port, force_tls, username, password, limit, category):
    """ Iterates over all applications and processes the maildir for each
    application that uses maildir e-mail delivery.

    """
    exit_code = 0

    class Mail(object):

        def __init__(self, maildir, filename):
            self.maildir = maildir
            self.filename = filename

        @cached_property
        def message(self):
            return email.message_from_string(self.text)

        @cached_property
        def text(self):
            return self.maildir.get_file(self.filename).read().decode('utf-8')

        @property
        def category(self):
            return self.message.get('X-Category')

        def remove(self):
            self.maildir.remove(self.filename)

        def send(self, connection):
            connection.sendmail(
                self.message['From'],
                self.message['To'],
                self.text)

            return connection.noop()[0]

    # applications with a maildir configuration
    cfgs = (c for c in group_context.appcfgs if 'mail' in c.configuration)
    cfgs = (v for c in cfgs for v in c.configuration['mail'].values())
    cfgs = (c for c in cfgs if c.get('use_directory'))

    # non-empty maildirs
    dirs = set(c['directory'] for c in cfgs)
    dirs = (mailbox.Maildir(d, create=False) for d in dirs)
    dirs = (d for d in dirs if len(d))

    # emails
    mails = (Mail(d, f) for d in dirs for f in d.keys())
    mails = (m for m in mails if category is None or m.category == category)

    # load all the mails we're going to process
    if limit:
        mails = tuple(x for _, x in zip(range(limit), mails))
    else:
        mails = tuple(mails)

    if not mails:
        sys.exit(exit_code)

    # create the connection handler
    postman = Postman(hostname, port)

    if force_tls:
        postman.middlewares.append(TLS(force=True))

    if username:
        postman.middlewares.append(Auth(username, password))

    # send the messages
    with postman.connection() as connection:

        for mail in mails:
            try:
                status = mail.send(connection)
            except SMTPRecipientsRefused as e:
                exit_code = 1
                print(f"Could not send e-mail: {e.recipients}")
                mail.remove()
            else:
                if status == 250:
                    mail.remove()

    sys.exit(exit_code)


@cli.command()
@click.argument('server')
@click.argument('remote-config')
@click.option('--confirm/--no-confirm', default=True,
              help="Ask for confirmation (disabling this is dangerous!)")
@click.option('--no-filestorage', default=False, is_flag=True,
              help="Do not transfer the files")
@click.option('--no-database', default=False, is_flag=True,
              help="Do not transfer the database")
@pass_group_context
def transfer(group_context,
             server, remote_config, confirm, no_filestorage, no_database):
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

    def download_folder(remote, local):
        tar_filename = '/tmp/{}.tar.gz'.format(uuid4().hex)

        subprocess.check_output([
            'ssh', server, '-C', "sudo tar czvf '{}' -C '{}' .".format(
                tar_filename, remote
            )
        ])

        subprocess.check_output([
            'scp',
            '{}:{}'.format(server, tar_filename),
            '{}/transfer.tar.gz'.format(local)
        ])

        subprocess.check_output([
            'tar', 'xzvf', '{}/transfer.tar.gz'.format(local),
            '-C', local
        ])

        subprocess.check_output([
            'ssh', server, '-C', "sudo rm '{}'".format(tar_filename)
        ])

        subprocess.check_output([
            'rm', '{}/transfer.tar.gz'.format(local)
        ])

    # filter out namespaces on demand
    for appcfg in group_context.appcfgs:

        if appcfg.configuration.get('disable_transfer'):
            print("Skipping {}, transfer disabled".format(appcfg.namespace))
            continue

        if appcfg.namespace not in remote_applications:
            print("Skipping {}, not found on remote".format(appcfg.namespace))
            continue

        remotecfg = remote_applications[appcfg.namespace]

        if not no_filestorage:
            if remotecfg.configuration.get('filestorage').endswith('OSFS'):
                assert appcfg.configuration.get('filestorage').endswith('OSFS')

                print("Fetching remote filestorage")

                local_fs = appcfg.configuration['filestorage_options']
                remote_fs = remotecfg.configuration['filestorage_options']

                remote_storage = os.path.join(
                    remote_dir, remote_fs['root_path'])
                local_storage = os.path.join('.', local_fs['root_path'])

                if ':'.join((remote_storage, local_storage)) in fetched:
                    continue

                download_folder(remote_storage, local_storage)

                fetched.add(':'.join((remote_storage, local_storage)))

            remote_backend = remotecfg.configuration.get('depot_backend')
            local_backend = appcfg.configuration.get('depot_backend')

            if remote_backend == 'depot.io.local.LocalFileStorage':
                assert local_backend == remote_backend

                print("Fetching depot storage")

                local_depot = appcfg.configuration['depot_storage_path']
                remote_depot = remotecfg.configuration['depot_storage_path']

                remote_storage = os.path.join(remote_dir, remote_depot)
                local_storage = os.path.join('.', local_depot)

                if ':'.join((remote_storage, local_storage)) in fetched:
                    continue

                download_folder(remote_storage, local_storage)

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


@cli.command(context_settings={'default_selector': '*'})
@click.option('--dry-run', default=False, is_flag=True,
              help="Do not write any changes into the database.")
@pass_group_context
def upgrade(group_context, dry_run):
    """ Upgrades all application instances of the given namespace(s). """

    modules = list(get_upgrade_modules())
    tasks = get_tasks()

    executed_raw_upgrades = set()

    basic_tasks = tuple((id, task) for id, task in tasks if not task.raw)
    raw_tasks = tuple((id, task) for id, task in tasks if task.raw)

    def on_success(task):
        print(click.style("* " + str(task.task_name), fg='green'))

    def on_fail(task):
        print(click.style("* " + str(task.task_name), fg='red'))

    def run_upgrade_runner(runner, *args):
        executed_tasks = runner.run_upgrade(*args)

        if executed_tasks:
            print("executed {} upgrade tasks".format(executed_tasks))
        else:
            print("no pending upgrade tasks found")

    def run_raw_upgrade(group_context, appcfg):
        if appcfg in executed_raw_upgrades:
            return

        executed_raw_upgrades.add(appcfg)

        title = "Running raw upgrade for {}".format(appcfg.path.lstrip('/'))
        print(click.style(title, underline=True))

        upgrade_runner = RawUpgradeRunner(
            tasks=raw_tasks,
            commit=not dry_run,
            on_task_success=on_success,
            on_task_fail=on_fail
        )

        run_upgrade_runner(
            upgrade_runner,
            appcfg.configuration['dsn'],
            group_context.available_schemas(appcfg),
        )

    def run_upgrade(request, app):
        title = "Running upgrade for {}".format(request.app.application_id)
        print(click.style(title, underline=True))

        upgrade_runner = UpgradeRunner(
            modules=modules,
            tasks=basic_tasks,
            commit=not dry_run,
            on_task_success=on_success,
            on_task_fail=on_fail
        )
        run_upgrade_runner(upgrade_runner, request)

    def upgrade_steps():
        if next((t for n, t in tasks if t.raw), False):
            yield run_raw_upgrade

        yield run_upgrade

    return tuple(upgrade_steps())
