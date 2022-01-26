import click
import os
import platform
import shutil
import subprocess
import sys

from fnmatch import fnmatch
from onegov.core.cache import lru_cache
from onegov.core.cli.core import command_group, pass_group_context, abort
from onegov.core.mail_processor import MailQueueProcessor
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import get_tasks
from onegov.core.upgrade import get_upgrade_modules
from onegov.core.upgrade import RawUpgradeRunner
from onegov.core.upgrade import UpgradeRunner
from onegov.server.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm.session import close_all_sessions


#: onegov.core's own command group
cli = command_group()


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes a single instance matching the selector.

    Selectors matching multiple organisations are disabled for saftey reasons.

    """

    def delete_instance(request, app):

        confirmation = "Do you really want to DELETE this instance?"

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        if app.has_filestorage:
            click.echo("Removing File Storage")

            for item in app.filestorage.listdir('.'):
                if app.filestorage.isdir(item):
                    app.filestorage.removedir(item)
                else:
                    app.filestorage.remove(item)

        if getattr(app, 'depot_storage_path', ''):
            if app.bound_storage_path:
                click.echo("Removing Depot Storage")
                shutil.rmtree(str(app.bound_storage_path.absolute()))

        if app.has_database_connection:
            click.echo("Dropping Database Schema")

            assert app.session_manager.is_valid_schema(app.schema)

            close_all_sessions()
            dsn = app.session_manager.dsn
            app.session_manager.dispose()

            engine = create_engine(dsn)
            engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
            engine.raw_connection().invalidate()
            engine.dispose()

        click.echo("Instance was deleted successfully")

    return delete_instance


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@click.option('--token', default=None,
              help="The postmark server token to authenticate")
@click.option('--limit', default=25,
              help="Max number of mails to send before exiting")
@pass_group_context
def sendmail(group_context, token, limit):
    """ Iterates over all applications and processes the maildir for each
    application that uses maildir e-mail delivery.

    """

    # applications with a maildir configuration
    cfgs = (c for c in group_context.appcfgs if 'mail' in c.configuration)
    cfgs = (v for c in cfgs for v in c.configuration['mail'].values())
    cfgs = (c for c in cfgs if c.get('directory'))

    # non-empty maildirs
    dirs = set(c['directory'] for c in cfgs)
    qp = MailQueueProcessor(token, *dirs, limit=limit)
    qp.send_messages()


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@click.argument('server')
@click.option('--remote-config', default='/var/lib/onegov-cloud/onegov.yml',
              help='Location of the remote config file')
@click.option('--confirm/--no-confirm', default=True,
              help="Ask for confirmation (disabling this is dangerous!)")
@click.option('--no-filestorage', default=False, is_flag=True,
              help="Do not transfer the files")
@click.option('--no-database', default=False, is_flag=True,
              help="Do not transfer the database")
@click.option('--transfer-schema', help="Only transfer this schema")
@pass_group_context
def transfer(group_context,
             server, remote_config, confirm, no_filestorage, no_database,
             transfer_schema):
    """ Transfers the database and all files from a server running a
    onegov-cloud application and installs them locally, overwriting the
    local data!

    This command expects to have access to the remote server via ssh
    (no password) and to be run sudo without password. If this is too scary
    for you, feel free to write something saner.

    Only namespaces which are present locally and remotely are considered.

    So if you have a 'cities' namespace locally and a 'towns' namespace on
    the remote, nothing will happen.

    It's also possible to transfer only a given schema, e.g. '/town/govikon' or
    '/town/*'. But beware, global files are copied in any case!

    WARNING: This may delete local content!

    """

    if transfer_schema:
        transfer_schema = transfer_schema.strip('/').replace('/', '-')

    if not shutil.which('pv'):
        print("")
        print("Core transfer requires 'pv', please install as follows:")
        print("* brew install pv")
        print("* apt-get install pv")
        print("")
        sys.exit(1)

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

        # GNUtar differs from MacOS's version somewhat and the combination
        # of parameters leads to a different strip components count. It seems
        # as if GNUtar will count the components after stripping, while MacOS
        # counts them before stripping
        count = remote.count('/')
        count += platform.system() == 'Darwin' and 1 or 0

        send = f"ssh {server} -C 'sudo nice -n 10 tar cz {remote}/{glob}'"
        send = f"{send} --absolute-names"
        recv = f"tar xz  --strip-components {count} -C {local}"

        if shutil.which('pv'):
            recv = f'pv -L 5m --name "{remote}/{glob}" -r -b | {recv}'

        print(f"Copying {remote}/{glob}")
        subprocess.check_output(f'{send} | {recv}', shell=True)

    def transfer_database(remote_db, local_db, schema_glob='*'):
        # Get available schemas
        query = 'SELECT schema_name FROM information_schema.schemata'

        lst = f'sudo -u postgres psql {remote_db} -t -c "{query}"'
        lst = f"ssh {server} '{lst}'"

        schemas = subprocess.check_output(lst, shell=True)
        schemas = (s.strip() for s in schemas.decode('utf-8').splitlines())
        schemas = (s for s in schemas if s)
        schemas = (s for s in schemas if fnmatch(s, schema_glob))
        schemas = tuple(schemas)

        # Prepare send command
        send = f"ssh {server} sudo -u postgres nice -n 10 pg_dump {remote_db}"
        send = f"{send} --no-owner --no-privileges"
        send = f"{send} --quote-all-identifiers --no-sync"
        send = f'{send} --schema {" --schema ".join(schemas)}'

        # Prepare receive command
        recv = f"psql -d {local_db} -v ON_ERROR_STOP=1"
        if platform.system() == 'Linux':
            recv = f"sudo -u postgres {recv}"

        # Drop existing schemas
        for schema in schemas:
            print(f"Drop local database schema {schema}")
            drop = f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'
            drop = f"echo '{drop}' | {recv}"

            subprocess.check_call(
                drop, shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Transfer
        print("Transfering database")
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

            transfer_storage(remote_storage, local_storage, glob='global-*')

            glob = transfer_schema or f'{local_cfg.namespace}*'
            transfer_storage(remote_storage, local_storage, glob=glob)

    def transfer_depot_storage_of_app(local_cfg, remote_cfg):
        depot_local_storage = 'depot.io.local.LocalFileStorage'
        remote_backend = remote_cfg.configuration.get('depot_backend')
        local_backend = local_cfg.configuration.get('depot_backend')

        if local_backend == remote_backend == depot_local_storage:
            local_depot = local_cfg.configuration['depot_storage_path']
            remote_depot = remote_cfg.configuration['depot_storage_path']

            remote_storage = os.path.join(remote_dir, remote_depot)
            local_storage = os.path.join('.', local_depot)

            glob = transfer_schema or f'{local_cfg.namespace}*'
            transfer_storage(remote_storage, local_storage, glob=glob)

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

        schema_glob = transfer_schema or f'{local_cfg.namespace}*'
        transfer_database(remote_db, local_db, schema_glob=schema_glob)

    # transfer the data
    for local_cfg in group_context.appcfgs:

        if transfer_schema and local_cfg.namespace not in transfer_schema:
            continue

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


@cli.command()
def shell():
    """ Enters the shell """

    def _shell(request, app):
        breakpoint()

    return _shell
