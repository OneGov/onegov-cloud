import click
import email
import mailbox
import os
import platform
import shutil
import subprocess
import sys

from cached_property import cached_property
from fnmatch import fnmatch
from mailthon.middleware import TLS, Auth
from onegov.core.cache import lru_cache
from onegov.core.cli.core import command_group, pass_group_context
from onegov.core.mail import Postman
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import get_tasks
from onegov.core.upgrade import get_upgrade_modules
from onegov.core.upgrade import RawUpgradeRunner
from onegov.core.upgrade import UpgradeRunner
from onegov.server.config import Config
from smtplib import SMTPRecipientsRefused


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


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
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

    try:
        remote_config = Config.from_yaml_string(
            subprocess.check_output([
                "ssh", server, "-C", "sudo cat '{}'".format(remote_config)
            ])
        )
    except subprocess.CalledProcessError:
        sys.exit(1)

    remote_applications = {a.namespace: a for a in remote_config.applications}

    # some calls to the storage transfer may be repeated as applications
    # share folders in certain configurations
    @lru_cache(maxsize=None)
    def transfer_storage(remote, local, glob='*'):
        send = f"ssh {server} -C 'sudo nice -n 10 tar cz {remote}/{glob}'"
        send = f"{send} --absolute-names"
        recv = f"tar xz  --strip-components {remote.count('/') + 1} -C {local}"

        if shutil.which('pv'):
            recv = f'pv --name "{remote}/{glob}" -r -b | {recv}'

        subprocess.check_output(f'{send} | {recv}', shell=True)

    def transfer_database(remote_db, local_db, schema_glob='*'):
        send = f"ssh {server} sudo -u postgres nice -n 10 pg_dump {remote_db}"
        send = f"{send} --no-owner --no-privileges"
        send = f"{send} --quote-all-identifiers --no-sync"

        recv = f"psql -d {local_db} -v ON_ERROR_STOP=1"

        query = 'SELECT schema_name FROM information_schema.schemata'

        lst = f'sudo -u postgres psql {remote_db} -t -c "{query}"'
        lst = f"ssh {server} '{lst}'"

        schemas = subprocess.check_output(lst, shell=True)
        schemas = (s.strip() for s in schemas.decode('utf-8').splitlines())
        schemas = (s for s in schemas if s)
        schemas = (s for s in schemas if fnmatch(s, schema_glob))
        schemas = tuple(schemas)

        send = f'{send} --schema {" --schema ".join(schemas)}'

        if platform.system() == 'Linux':
            recv = f"sudo -u postgres {recv}"

        for schema in schemas:
            drop = f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'
            drop = f"echo '{drop}' | {recv}"

            subprocess.check_call(
                drop, shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)

        if shutil.which('pv'):
            recv = f'pv --name "{remote_db}@postgres" -r -b | {recv}'

        subprocess.check_output(f'{send} | {recv}', shell=True)

    def transfer_storage_of_app(local_cfg, remote_cfg):

        remote_storage = remote_cfg.configuration.get('filestorage')
        local_storage = local_cfg.configuration.get('filestorage')

        if remote_storage.endswith('OSFS') and local_storage.endswith('OSFS'):
            local_fs = local_cfg.configuration['filestorage_options']
            remote_fs = remote_cfg.configuration['filestorage_options']

            remote_storage = os.path.join(remote_dir, remote_fs['root_path'])
            local_storage = os.path.join('.', local_fs['root_path'])

            transfer_storage(
                remote_storage, local_storage, glob=f'global-*')

            transfer_storage(
                remote_storage, local_storage, glob=f'{local_cfg.namespace}*')

    def transfer_depot_storage_of_app(local_cfg, remote_cfg):

        depot_local_storage = 'depot.io.local.LocalFileStorage'
        remote_backend = remote_cfg.configuration.get('depot_backend')
        local_backend = local_cfg.configuration.get('depot_backend')

        if local_backend == remote_backend == depot_local_storage:
            local_depot = local_cfg.configuration['depot_storage_path']
            remote_depot = remote_cfg.configuration['depot_storage_path']

            remote_storage = os.path.join(remote_dir, remote_depot)
            local_storage = os.path.join('.', local_depot)

            transfer_storage(
                remote_storage, local_storage, glob=f'{local_cfg.namespace}*')

    def transfer_database_of_app(local_cfg, remote_cfg):
        if 'dsn' not in remote_cfg.configuration:
            return

        if 'dsn' not in local_cfg.configuration:
            return

        # on an empty database we need to create the extensions first
        mgr = SessionManager(local_cfg.configuration['dsn'], Base)
        mgr.create_required_extensions()

        local_db = local_cfg.configuration['dsn'].split('/')[-1]
        remote_db = remote_cfg.configuration['dsn'].split('/')[-1]

        transfer_database(
            remote_db, local_db, schema_glob=f'{local_cfg.namespace}*')

    # transfer the data
    for local_cfg in group_context.appcfgs:

        if local_cfg.namespace not in remote_applications:
            continue

        if local_cfg.configuration.get('disable_transfer'):
            print(f"Skipping {local_cfg.namespace}, transfer disabled")
            continue

        remote_cfg = remote_applications[local_cfg.namespace]

        print(f"Fetching {remote_cfg.namespace}")

        if not no_filestorage:
            transfer_storage_of_app(local_cfg, remote_cfg)
            transfer_depot_storage_of_app(local_cfg, remote_cfg)

        if not no_database:
            transfer_database_of_app(local_cfg, remote_cfg)

    if not shutil.which('pv'):
        print("")
        print("TIP: To get better output with transfer rates, install pv:")
        print("brew install pv")
        print("")


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
