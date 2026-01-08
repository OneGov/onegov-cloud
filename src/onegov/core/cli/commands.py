from __future__ import annotations

import click
import os
import platform
import shlex
import shutil
import smtplib
import ssl
import subprocess
from code import InteractiveConsole
import sys
import readline
import rlcompleter
from collections import defaultdict
from fnmatch import fnmatch
from functools import cache
from onegov.core import log
from onegov.core.cli.core import (
    abort, command_group, pass_group_context, run_processors)
from onegov.core.crypto import hash_password
from onegov.core.mail_processor import PostmarkMailQueueProcessor
from onegov.core.mail_processor import SMTPMailQueueProcessor
from onegov.core.sms_processor import SmsQueueProcessor
from onegov.core.sms_processor import get_sms_queue_processor
from onegov.core.orm import Base, SessionManager
from onegov.core.upgrade import get_tasks
from onegov.core.upgrade import get_upgrade_modules
from onegov.core.upgrade import RawUpgradeRunner
from onegov.core.upgrade import UpgradeRunner
from onegov.server.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm.session import close_all_sessions
from time import sleep
from transaction import commit
from urllib.parse import urlparse
from uuid import uuid4
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from watchdog.events import FileSystemEvent

    from onegov.core.cli.core import GroupContext
    from onegov.core.framework import Framework
    from onegov.core.mail_processor.core import MailQueueProcessor
    from onegov.core.request import CoreRequest
    from onegov.core.upgrade import _Task
    from onegov.server.config import ApplicationConfig


#: onegov.core's own command group
cli = command_group()


@cli.command()
@pass_group_context
def delete(
    group_context: GroupContext
) -> Callable[[CoreRequest, Framework], None]:
    """ Deletes a single instance matching the selector.

    Selectors matching multiple organisations are disabled for saftey reasons.

    """

    def delete_instance(request: CoreRequest, app: Framework) -> None:

        confirmation = 'Do you really want to DELETE this instance?'

        if not click.confirm(confirmation):
            abort('Deletion process aborted')

        if app.has_filestorage:
            click.echo('Removing File Storage')
            assert app.filestorage is not None
            for item in app.filestorage.listdir('.'):
                if app.filestorage.isdir(item):
                    app.filestorage.removetree(item)
                else:
                    app.filestorage.remove(item)

        if getattr(app, 'depot_storage_path', ''):
            assert hasattr(app, 'bound_storage_path')
            if app.bound_storage_path:
                click.echo('Removing Depot Storage')
                shutil.rmtree(str(app.bound_storage_path.absolute()))

        if app.has_database_connection:
            click.echo('Dropping Database Schema')

            assert app.session_manager.is_valid_schema(app.schema)

            close_all_sessions()
            dsn = app.session_manager.dsn
            app.session_manager.dispose()

            engine = create_engine(dsn)
            engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
            engine.raw_connection().invalidate()
            engine.dispose()

        click.echo(
            'Instance was deleted successfully. Please flush redis and '
            'restart the service(s) to make sure that there are no stale '
            'database definitions used in running instances.'
        )

    return delete_instance


@cli.group(invoke_without_command=True, context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@click.option('--queue', default='postmark',
              help='The name of the queue to process')
@click.option('--limit', default=25,
              help='Max number of mails to send before exiting')
@pass_group_context
def sendmail(group_context: GroupContext, queue: str, limit: int) -> None:
    """ Sends mail from a specific mail queue. """

    queues = group_context.config.mail_queues
    if queue not in queues:
        click.echo(f'The queue "{queue}" does not exist.', err=True)
        sys.exit(1)

    cfg = queues[queue]
    mailer = cfg.get('mailer', 'postmark')
    directory = cfg.get('directory')
    if not directory:
        click.echo('No directory configured for this queue.', err=True)
        sys.exit(1)

    qp: MailQueueProcessor
    if mailer == 'postmark':
        qp = PostmarkMailQueueProcessor(cfg['token'], directory, limit=limit)
        qp.send_messages()

    elif mailer == 'smtp':
        with smtplib.SMTP(cfg['host'], cfg['port']) as mailer:
            if cfg.get('force_tls', False):
                context = ssl.create_default_context()
                mailer.starttls(context=context)

            username = cfg.get('username')
            if username is not None:
                mailer.login(username, cfg.get('password'))

            qp = SMTPMailQueueProcessor(mailer, directory, limit=limit)
            qp.send_messages()
    else:
        click.echo(f'Unknown mailer {mailer} specified in config.', err=True)
        sys.exit(1)


@cli.group(context_settings={
    'matches_required': False,
    'skip_search_indexing': True,
    'default_selector': '*'
})
@pass_group_context
def sendsms(
    group_context: GroupContext
) -> Callable[[CoreRequest, Framework], None]:
    """ Sends the SMS in the smsdir for a given instance.

    For example::

        onegov-core --select '/onegov_town6/meggen' sendsms

    """

    def send(request: CoreRequest, app: Framework) -> None:
        qp = get_sms_queue_processor(app)
        if qp is None:
            return

        qp.send_messages()

    return send


class SmsEventHandler(PatternMatchingEventHandler):

    def __init__(self, queue_processors: list[SmsQueueProcessor]):
        self.queue_processors = queue_processors
        super().__init__(
            ignore_patterns=['*.sending-*', '*.rejected-*', '*/tmp/*'],
            ignore_directories=True
        )

    def on_moved(self, event: FileSystemEvent) -> None:
        dest_path = os.path.abspath(str(event.dest_path))
        assert isinstance(dest_path, str)
        for qp in self.queue_processors:
            # only one queue processor should match
            if dest_path.startswith(qp.path):
                try:
                    qp.send_messages()
                except Exception:
                    log.exception(
                        'Encountered fatal exception when sending messages'
                    )
                return

    # NOTE: In the vast majority of cases the trigger will be a file system
    #       move since our DataManager creates a temporary file that then is
    #       moved. But we should also trigger when new files are created just
    #       in case this ever changes.
    def on_created(self, event: FileSystemEvent) -> None:
        src_path = os.path.abspath(str(event.src_path))
        assert isinstance(src_path, str)
        for qp in self.queue_processors:
            # only one queue processor should match
            if src_path.startswith(qp.path):
                try:
                    qp.send_messages()
                except Exception:
                    log.exception(
                        'Encountered fatal exception when sending messages'
                    )
                return


@cli.group(invoke_without_command=True, context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@pass_group_context
def sms_spooler(group_context: GroupContext) -> None:
    """ Continuously spools the SMS in the smsdir for all instances using
    a watchdog that monitors the smsdir for newly created files.

    For example::

        onegov-core sms-spooler
    """

    queue_processors: dict[str, list[SmsQueueProcessor]] = defaultdict(list)

    def create_sms_queue_processor(
        request: CoreRequest,
        app: Framework
    ) -> None:

        # we're fine if the path doesn't exist yet, we only call
        # qp.send_messages() when changes inside the path occur
        qp = get_sms_queue_processor(app, missing_path_ok=True)
        if qp is not None:
            assert app.sms_directory
            path = os.path.abspath(app.sms_directory)
            queue_processors[path].append(qp)

    run_processors(group_context, (create_sms_queue_processor,))
    if not queue_processors:
        abort('No SMS delivery configured for the specified selector')

    observer = Observer()
    for sms_directory, qps in queue_processors.items():
        event_handler = SmsEventHandler(qps)
        observer.schedule(event_handler, sms_directory, recursive=True)

    observer.start()
    log.info('Spooler initialized')
    # make sure any setup on the observer thread has a chance to happen
    sleep(0.1)

    # after starting the observer we call send on all our queues, so we
    # don't delay sending messages that have been queued between restarts
    # of this spooler
    for qps in queue_processors.values():
        for qp in qps:
            # the directory of the queue processor might not exist yet
            # we only need to send messages if it exists
            if os.path.exists(qp.path):
                qp.send_messages()

    # run observer until we receive something like a KeyboardInterrupt
    # or a SIGKILL
    try:
        while True:
            sleep(1)
    finally:
        observer.stop()
        observer.join()


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
@click.argument('server')
@click.option('--remote-config', default='/var/lib/onegov-cloud/onegov.yml',
              help='Location of the remote config file')
@click.option('--confirm/--no-confirm', default=True,
              help='Ask for confirmation (disabling this is dangerous!)')
@click.option('--no-filestorage', default=False, is_flag=True,
              help='Do not transfer the files')
@click.option('--no-database', default=False, is_flag=True,
              help='Do not transfer the database')
@click.option('--transfer-schema',
              help='Only transfer this schema, e.g. /town6/govikon')
@click.option('--add-admins', default=False, is_flag=True,
              help='Add local admins (admin@example.org:test)')
@click.option('--delta', default=False, is_flag=True,
              help='Only transfer files where size or modification time '
                   'changed')
@pass_group_context
def transfer(
    group_context: GroupContext,
    server: str,
    remote_config: str,
    confirm: bool,
    no_filestorage: bool,
    no_database: bool,
    transfer_schema: str | None,
    add_admins: bool,
    delta: bool
) -> None:
    """ Transfers the database and all files from a server running a
    onegov-cloud application and installs them locally, overwriting the
    local data!

    This command expects to have access to the remote server via ssh
    (no password) and to be run sudo without password. If this is too scary
    for you, feel free to write something saner.

    Only namespaces which are present locally and remotely are considered.

    So if you have a 'cities' namespace locally and a 'towns' namespace on
    the remote, nothing will happen.

    It's also possible to transfer only a given schema, e.g. ``/town6/govikon``
    or ``/town6/*``. But beware, global files are copied in any case!

    WARNING: This may delete local content!

    """

    if transfer_schema:
        transfer_schema = transfer_schema.strip('/').replace('/', '-')

    if delta and not shutil.which('rsync'):
        click.echo('')
        click.echo("Core delta transfer requires 'rsync', please install as "
                   "follows:")
        click.echo('* brew install rsync')
        click.echo('* apt-get install rsync')
        click.echo('')
        sys.exit(1)

    if not shutil.which('pv'):
        click.echo('')
        click.echo("Core transfer requires 'pv', please install as follows:")
        click.echo('* brew install pv')
        click.echo('* apt-get install pv')
        click.echo('')
        sys.exit(1)

    if no_filestorage and delta:
        raise click.UsageError(
            'You cannot use --no-filestorage and --delta together because '
            '--no-filestorage skips all file storage transfers, while '
            '--delta requires transferring only modified files.'
        )

    if confirm:
        click.confirm(
            'Do you really want override all your local data?',
            default=False, abort=True
        )

    click.echo('Parsing the remote application configuration')

    remote_dir = os.path.dirname(remote_config)

    try:
        remote_cfg = Config.from_yaml_string(
            # NOTE: Using an absolute path is more trouble than it's worth
            subprocess.check_output([  # nosec
                'ssh', server, '-C', 'sudo cat {}'.format(
                    shlex.quote(remote_config)
                )
            ])
        )
    except subprocess.CalledProcessError:
        sys.exit(1)

    remote_applications = {a.namespace: a for a in remote_cfg.applications}

    # some calls to the storage transfer may be repeated as applications
    # share folders in certain configurations
    @cache
    def transfer_storage(remote: str, local: str, glob: str = '*') -> None:

        # GNUtar differs from MacOS's version somewhat and the combination
        # of parameters leads to a different strip components count. It seems
        # as if GNUtar will count the components after stripping, while MacOS
        # counts them before stripping
        count = remote.count('/')
        count += platform.system() == 'Darwin' and 1 or 0

        send = shlex.join([
            'ssh',
            server,
            '-C',
            shlex.join([
                'sudo',
                'nice',
                '-n',
                '10',
                'tar',
                'cz',
                f'{remote}/{glob}',
                '--absolute-names',
            ]),
        ])
        recv = shlex.join([
            'tar',
            'xz',
            '--strip-components',
            str(count),
            '-C',
            local,
        ])

        if shutil.which('pv'):
            track_progress = shlex.join([
                'pv',
                '-L',
                '5m',
                '--name',
                f'{remote}/{glob}',
                '-r',
                '-b',
            ])
            recv = f'{track_progress} | {recv}'

        click.echo(f'Copying {remote}/{glob}')
        # NOTE: We took extra care that this is safe with shlex.join
        subprocess.check_output(f'{send} | {recv}', shell=True)  # nosec:B602

    @cache
    def transfer_delta_storage(
        remote: str, local: str, glob: str = '*'
    ) -> None:
        """ Transfers only changed files based on size or last-modified
        time. This is rsnyc default behaviour. """

        # '/***' means to include all files and directories under a directory
        # recursively. Without that, it will only transfer the directory but
        # not it's contents.
        glob += '/***'

        dry_run = shlex.join([
            'rsync',
            '-a',
            "--include='*/'",
            '--include={}'.format(shlex.quote(glob)),
            "--exclude='*'",
            '--dry-run',
            '--itemize-changes',
            f'{server}:{remote}/',
            f'{local}/',
        ])
        # NOTE: We took extra care that this is safe with shlex.join
        subprocess.run(dry_run, shell=True, capture_output=False)  # nosec:B602

        send = shlex.join([
            'rsync',
            '-av',
            "--include='*/'",
            '--include={}'.format(shlex.quote(glob)),
            "--exclude='*'",
            f'{server}:{remote}/',
            f'{local}/',
        ])

        if shutil.which('pv'):
            track_progress = shlex.join([
                'pv',
                '-L',
                '5m',
                '--name',
                f'{remote}/{glob}',
                '-r',
                '-b',
            ])
            send = f'{send} | {track_progress}'
        click.echo(f'Copying {remote}/{glob}')
        # NOTE: We took extra care that this is safe with shlex.join
        subprocess.check_output(send, shell=True)  # nosec:B602

    def transfer_database(
        remote_db: str,
        local_db: str,
        local_dsn: str,
        schema_glob: str = '*'
    ) -> tuple[str, ...]:

        parsed = urlparse(local_dsn)
        local_host = parsed.hostname or 'localhost'
        local_port = str(parsed.port or 5432)
        local_user = parsed.username or 'postgres'
        local_password = parsed.password or ''

        # Get available schemas
        query = 'SELECT schema_name FROM information_schema.schemata'

        lst = shlex.join([
            'sudo',
            '-u',
            'postgres',
            'psql',
            remote_db,
            '-t',
            '-c',
            query,
        ])
        lst = shlex.join([
            'ssh',
            server,
            lst,
        ])

        # NOTE: We took extra care that this is safe with shlex.join
        schemas_str = subprocess.check_output(
            lst, shell=True  # nosec:B602
        ).decode('utf-8')
        schemas_iter = (s.strip() for s in schemas_str.splitlines())
        schemas_iter = (s for s in schemas_iter if s)
        schemas_iter = (s for s in schemas_iter if fnmatch(s, schema_glob))
        schemas = tuple(schemas_iter)

        if not schemas:
            click.echo('No matching schema(s) found!')
            return schemas

        # Prepare send command
        send_parts = [
            'sudo',
            '-u',
            'postgres',
            'nice',
            '-n',
            '10',
            'pg_dump',
            remote_db,
            '--no-owner',
            '--no-privileges',
            '--quote-all-identifiers',
            '--no-sync',
        ]
        for schema in schemas:
            send_parts.extend(('--schema', schema))

        send = shlex.join(send_parts)
        send = shlex.join([
            'ssh',
            server,
            send,
        ])

        # Prepare receive command
        recv_parts = [
            'psql',
            '-h',
            local_host,
            '-p',
            local_port,
            '-U',
            local_user,
            '-d',
            local_db,
            '-v',
            'ON_ERROR_STOP=1',
        ]

        recv = shlex.join(recv_parts)

        # Drop existing schemas
        for schema in schemas:
            click.echo(f'Drop local database schema {schema}')
            assert "'" not in schema and '"' not in schema
            drop = f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'
            drop = f"echo '{drop}' | {recv}"

            subprocess.check_call(  # nosec:B602
                drop,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, 'PGPASSWORD': local_password}
            )

        # Transfer
        click.echo('Transfering database')
        if shutil.which('pv'):
            track_progress = shlex.join([
                'pv',
                '--name',
                f'{remote_db}@postgres',
                '-r',
                '-b',
            ])
            recv = f'{track_progress} | {recv}'
        # NOTE: We took extra care that this is safe with shlex.join
        subprocess.check_output(
            f'{send} | {recv}',
            shell=True,  # nosec:B602
            env={**os.environ, 'PGPASSWORD': local_password}
        )

        return schemas

    def transfer_storage_of_app(
        local_cfg: ApplicationConfig,
        remote_cfg: ApplicationConfig,
        transfer_function: Callable[..., None]
    ) -> None:

        remote_storage = remote_cfg.configuration.get('filestorage', '')
        local_storage = local_cfg.configuration.get('filestorage', '')

        if remote_storage.endswith('OSFS') and local_storage.endswith('OSFS'):
            local_fs = local_cfg.configuration['filestorage_options']
            remote_fs = remote_cfg.configuration['filestorage_options']

            remote_storage = os.path.join(remote_dir, remote_fs['root_path'])
            local_storage = os.path.join('.', local_fs['root_path'])

            transfer_function(remote_storage, local_storage, glob='global-*')

            glob = transfer_schema or f'{local_cfg.namespace}*'
            transfer_function(remote_storage, local_storage, glob=glob)

    def transfer_depot_storage_of_app(
        local_cfg: ApplicationConfig,
        remote_cfg: ApplicationConfig,
        transfer_function: Callable[..., None]
    ) -> None:

        depot_local_storage = 'depot.io.local.LocalFileStorage'
        remote_backend = remote_cfg.configuration.get('depot_backend')
        local_backend = local_cfg.configuration.get('depot_backend')

        if local_backend == remote_backend == depot_local_storage:
            local_depot = local_cfg.configuration['depot_storage_path']
            remote_depot = remote_cfg.configuration['depot_storage_path']

            remote_storage = os.path.join(remote_dir, remote_depot)
            local_storage = os.path.join('.', local_depot)

            glob = transfer_schema or f'{local_cfg.namespace}*'
            transfer_function(remote_storage, local_storage, glob=glob)

    def transfer_database_of_app(
        local_cfg: ApplicationConfig,
        remote_cfg: ApplicationConfig
    ) -> tuple[str, ...]:

        if 'dsn' not in remote_cfg.configuration:
            return ()

        if 'dsn' not in local_cfg.configuration:
            return ()

        # on an empty database we need to create the extensions first
        mgr = SessionManager(local_cfg.configuration['dsn'], Base)
        mgr.create_required_extensions()

        local_dsn = local_cfg.configuration['dsn']
        local_db = local_dsn.split('/')[-1]
        remote_db = remote_cfg.configuration['dsn'].split('/')[-1]

        schema_glob = transfer_schema or f'{local_cfg.namespace}*'
        return transfer_database(
            remote_db, local_db, local_dsn, schema_glob=schema_glob
        )

    def do_add_admins(local_cfg: ApplicationConfig, schema: str) -> None:
        id_ = str(uuid4())
        password_hash = hash_password('test')
        assert '"' not in schema and "'" not in schema
        query = (
            f'INSERT INTO "{schema}".users '  # nosec: B608
            f"(type, id, username, password_hash, role, active, realname) "
            f"VALUES ('generic', '{id_}', 'admin@example.org', "
            f"'{password_hash}', 'admin', true, 'John Doe');"
        )
        local_dsn = local_cfg.configuration['dsn']
        local_db = local_dsn.split('/')[-1]

        parsed = urlparse(local_dsn)
        local_host = parsed.hostname or 'localhost'
        local_port = str(parsed.port or 5432)
        local_user = parsed.username or 'postgres'
        local_password = parsed.password or ''

        command = shlex.join([
            'psql',
            '-h',
            local_host,
            '-p',
            local_port,
            '-U',
            local_user,
            '-d',
            local_db,
            '-c',
            query,
        ])
        # NOTE: We took extra care that this is safe with shlex.join
        subprocess.check_call(  # nosec:B602
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, 'PGPASSWORD': local_password}
        )

    # transfer the data
    schemas: set[str] = set()
    for local_appcfg in group_context.appcfgs:

        if transfer_schema and local_appcfg.namespace not in transfer_schema:
            continue

        if local_appcfg.namespace not in remote_applications:
            continue

        if local_appcfg.configuration.get('disable_transfer'):
            click.echo(f'Skipping {local_appcfg.namespace}, transfer disabled')
            continue

        remote_appcfg = remote_applications[local_appcfg.namespace]

        click.echo(f'Fetching {remote_appcfg.namespace}')

        if not no_database:
            schemas.update(
                transfer_database_of_app(local_appcfg, remote_appcfg))

        if not no_filestorage:
            transfer_strategy = (transfer_delta_storage if delta else
                                 transfer_storage)
            transfer_storage_of_app(
                local_appcfg, remote_appcfg, transfer_strategy
            )
            transfer_depot_storage_of_app(
                local_appcfg, remote_appcfg, transfer_strategy
            )

    if add_admins:
        for schema in schemas:
            click.echo(f'Adding admin@example:test to {schema}')
            # FIXME: This is a bit sus, it works because we only access
            #        the DSN of the app config and it's the same for all
            #        the app configs, we should be a bit more explicit that
            #        we are passing a shared configuration value, rather
            #        than an application specific one
            do_add_admins(local_appcfg, schema)


@cli.command(context_settings={'default_selector': '*'})
@click.option('--dry-run', default=False, is_flag=True,
              help='Do not write any changes into the database.')
@pass_group_context
def upgrade(
    group_context: GroupContext,
    dry_run: bool
) -> tuple[Callable[..., Any], ...]:
    """ Upgrades all application instances of the given namespace(s). """

    modules = list(get_upgrade_modules())
    tasks = get_tasks()

    executed_raw_upgrades = set()

    basic_tasks = tuple((id, task) for id, task in tasks if not task.raw)
    raw_tasks = tuple((id, task) for id, task in tasks if task.raw)

    def on_success(task: _Task[..., Any]) -> None:
        click.secho(f'* {task.task_name}', fg='green')

    def on_fail(task: _Task[..., Any]) -> None:
        click.secho(f'* {task.task_name}', fg='red')

    def run_upgrade_runner(
        runner: UpgradeRunner | RawUpgradeRunner,
        *args: Any
    ) -> None:
        executed_tasks = runner.run_upgrade(*args)

        if executed_tasks:
            click.echo('executed {} upgrade tasks'.format(executed_tasks))
        else:
            click.echo('no pending upgrade tasks found')

    def run_raw_upgrade(
        group_context: GroupContext,
        appcfg: ApplicationConfig
    ) -> None:

        if appcfg in executed_raw_upgrades:
            return

        executed_raw_upgrades.add(appcfg)

        title = 'Running raw upgrade for {}'.format(appcfg.path.lstrip('/'))
        click.secho(title, underline=True)

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

    def run_upgrade(request: CoreRequest, app: Framework) -> None:
        title = 'Running upgrade for {}'.format(request.app.application_id)
        click.secho(title, underline=True)

        upgrade_runner = UpgradeRunner(
            modules=modules,
            tasks=basic_tasks,
            commit=not dry_run,
            on_task_success=on_success,
            on_task_fail=on_fail
        )
        run_upgrade_runner(upgrade_runner, request)

    def upgrade_steps() -> Iterator[Callable[..., Any]]:
        if next((t for n, t in tasks if t.raw), False):
            yield run_raw_upgrade

        yield run_upgrade

    return tuple(upgrade_steps())


class EnhancedInteractiveConsole(InteractiveConsole):
    """ Wraps the InteractiveConsole with some basic shell features:

    - horizontal movement (e.g. arrow keys)
    - history (e.g. up and down keys)
    - very basic tab completion
    """

    def __init__(self, locals: dict[str, Any] | None = None):
        super().__init__(locals)
        self.init_completer()

    def init_completer(self) -> None:
        readline.set_completer(
            rlcompleter.Completer(
                dict(self.locals) if self.locals else {}
            ).complete
        )
        readline.set_history_length(100)
        readline.parse_and_bind('tab: complete')


@cli.command()
def shell() -> Callable[[CoreRequest, Framework], None]:
    """ Enters an interactive shell. """

    def _shell(request: CoreRequest, app: Framework) -> None:

        shell = EnhancedInteractiveConsole({
            'app': app,
            'request': request,
            'session': app.session(),
            'commit': commit
        })
        shell.interact(banner="""
        Onegov Cloud Shell
        ==================

        Exit the console using exit() or quit().

        Available variables: app, request, session.
        Available functions: commit

        Example:
           from onegov.user import User
           query = session.query(User).filter_by(username='admin@example.org')
           user = query.one()
           user.username = 'info@example.org'
           commit()
           exit()
        """)

    return _shell
