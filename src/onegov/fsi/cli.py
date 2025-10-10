from __future__ import annotations

import click
import json
import transaction

from datetime import date, datetime, UTC
from sedate import replace_timezone
from sqlalchemy import or_, and_
from sqlalchemy import cast, Date

from onegov.core.cli import command_group
from onegov.fsi import log
from onegov.fsi.ims_import import (
    parse_ims_data, import_ims_data, import_teacher_data, with_open,
    parse_date, validate_integer, parse_status)
from onegov.fsi.models import CourseAttendee, CourseEvent
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user import User
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.provider import ensure_user
from onegov.user.sync import ZugUserSource


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from ldap3.core.connection import Connection as LDAPConnection
    from onegov.core.csv import CSVFile, DefaultRow
    from onegov.fsi.app import FsiApp
    from onegov.fsi.request import FsiRequest
    from sqlalchemy.orm import Session
    from uuid import UUID


cli = command_group()


def do_ims_import(path: str, request: FsiRequest) -> None:
    _errors, persons, courses, events, possible_ldap_users = parse_ims_data(
        f'{path}/Teilnehmer.txt',
        f'{path}/Ausführungen.txt',
        f'{path}/Kurse.txt',
        f'{path}/Personen.txt'
    )
    assert persons is not None
    assert courses is not None
    assert events is not None
    assert possible_ldap_users is not None
    statistics = import_ims_data(
        request.session, persons, courses, events, possible_ldap_users)
    for key, val in statistics.items():
        click.secho(f'{key}: {val}')


@cli.command(name='import-ims-data', context_settings={'singular': True})
@click.option('--path', help='Path with pre-named files', required=True)
def import_ims_data_cli(path: str) -> Callable[[FsiRequest, FsiApp], None]:

    def execute(request: FsiRequest, app: FsiApp) -> None:
        do_ims_import(path, request)
    return execute


@cli.command(name='correct-ims-data', context_settings={'singular': True})
@click.option('--path', help='Path Ausführungen.txt', required=False)
def correct_ims_data_cli(path: str) -> Callable[[FsiRequest, FsiApp], None]:

    def fix_original_ims_import(request: FsiRequest, app: FsiApp) -> None:
        # Import of data was done according to timestamps 15.01.2020
        session = request.session

        def delete_events_without_subscriptions(
            session: Session
        ) -> tuple[int, int]:
            query = session.query(CourseEvent).filter(
                cast(CourseEvent.created, Date) == date(2020, 1, 15)
            )
            total = query.count()
            deleted = 0
            for event in query:
                if event.attendees.count() == 0:
                    deleted += 1
                    session.delete(event)
            return total, deleted

        def parse_date_correct(val: str | None) -> datetime | None:
            if not val:
                return None
            date_ = datetime.strptime(val, '%d/%m/%Y %H:%M:%S')
            return replace_timezone(date_, 'UTC')

        def correct_datetime(dt: datetime) -> datetime:
            return datetime(
                dt.year,
                dt.day,
                dt.month,
                dt.hour,
                dt.minute,
                tzinfo=UTC)

        @with_open
        def open_events_file(
            csvfile: CSVFile[DefaultRow],
            session: Session
        ) -> tuple[set[UUID], list[str]]:
            corrected_event_ids: set[UUID] = set()
            control_messages: list[str] = []
            for line in csvfile.lines:
                date_lacking = not line.kurs_von or not line.kurs_bis
                if date_lacking:
                    continue

                start = parse_date(line.kurs_von)
                correct_start = parse_date_correct(line.kurs_von)
                min_att = validate_integer(line.teilnehmer_min)
                max_att = validate_integer(line.teilnehmer_max)
                buchungsstatus = line.buchungsstatus
                if (
                    start == correct_start
                    or buchungsstatus == 'Keine Buchungen'
                ):
                    continue

                events_q = session.query(CourseEvent).filter_by(
                    start=start,
                    min_attendees=min_att,
                    max_attendees=max_att,
                    status=parse_status(line.status)
                )
                if corrected_event_ids:
                    events_q = events_q.filter(
                        CourseEvent.id.notin_(corrected_event_ids)
                    )

                events = events_q.all()

                if events:
                    names = []
                    for ev in events:
                        # be sure that there are not duplicate courses!!!
                        course_name = ev.course.name
                        assert course_name not in names
                        names.append(course_name)

                    # correct events and register them as changed
                    for event in events:
                        corrected_event_ids.add(event.id)
                        new_start = correct_datetime(event.start)
                        assert new_start == correct_start
                        event.start = correct_datetime(event.start)
                        event.end = correct_datetime(event.end)

            # corrected using the created data
            to_change_ids = set()
            by_created_query = session.query(CourseEvent).filter(
                cast(CourseEvent.created, Date) == date(2020, 1, 15)
            )
            for event in by_created_query:
                start = event.start
                if start.day < 13 and start.day != start.month:
                    to_change_ids.add(event.id)
            click.echo(
                f'To correct by using created date: {len(to_change_ids)}'
            )
            assert len(to_change_ids) == len(corrected_event_ids)

            return corrected_event_ids, control_messages

        # delete old course events
        total, deleted_count = delete_events_without_subscriptions(session)
        session.flush()
        click.echo(
            f'Deleted course events without subs: {deleted_count}/{total}'
        )
        corrected_ids, _ctrl_msgs = open_events_file(path, session)
        session.flush()

        click.echo(f'Corrected course events using '
              f'original file: {len(corrected_ids)}')

        with open('changed_events.log', 'w') as log_file:
            click.echo('\n'.join(str(i) for i in corrected_ids), file=log_file)

    return fix_original_ims_import


@cli.command(name='import-teacher-data', context_settings={'singular': True})
@click.option('--path', help='Filepath', required=True)
@click.option('--clear', is_flag=True, default=False,
              help='Clear imported data')
def import_teacher_data_cli(
    path: str,
    clear: bool
) -> Callable[[FsiRequest, FsiApp], None]:

    def execute(request: FsiRequest, app: FsiApp) -> None:
        import_teacher_data(path, request, clear)
    return execute


@cli.command(name='test-ldap')
@click.option('--base', multiple=True)
@click.option('--search-filter', default='')
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
@click.option('--sort-by', required=True, default='mail')
def test_ldap(
    base: Sequence[str],
    search_filter: str,
    ldap_server: str,
    ldap_username: str,
    ldap_password: str,
    sort_by: str
) -> None:
    r"""
    Examples:

        * Search for an email: ``(mail=walter.roderer@zg.ch)``
        * Search for names: ``(&(zgXGivenName=Vorname)(zgXSurname=Nachname))``
        * Search for mail ending in: ``(mail=*@phgz.ch)``

    .. code-block:: bash

        onegov-fsi --select /fsi/zug test-ldap --base 'ou=Kanton,o=KTZG' \
          --ldap-server 'ldaps://.....' \
          --ldap-username 'user' \
          --ldap-password 'xxxx' --search-filter "(mail=*@zg.ch)"

    """

    def sort_func(entry: Any) -> Any:
        return entry.entry_attributes_as_dict[sort_by]

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()
    mapping = {
        'uid': 'source_id',
        'zgXGivenName': 'first_name',
        'zgXSurname': 'last_name',
        'mail': 'mail',
        'zgXDirektionAbk': 'directorate',
        'zgXAmtAbk': 'agency',
        'zgXAbteilung': 'department',
    }
    attributes = [*mapping.keys(), 'groupMembership', 'zgXServiceSubscription']
    count = 0
    for ba in base:
        success = client.connection.search(
            ba, search_filter, attributes=attributes)
        if not success:
            click.echo(f'Search not successfull in base {ba}')
            continue
        for ix, entry in enumerate(
            sorted(client.connection.entries, key=sort_func)
        ):
            click.echo(json.dumps(entry.entry_attributes_as_dict, indent=4))
            count += 1
    click.echo(f'Found {count} entries')


@cli.command(name='fetch-users', context_settings={'singular': True})
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
@click.option('--admin-group', required=True, help='group id for role admin')
@click.option('--editor-group', required=True, help='group id for role editor')
@click.option('--verbose', is_flag=True, default=False)
@click.option('--skip-deactivate', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False)
def fetch_users_cli(
    ldap_server: str,
    ldap_username: str,
    ldap_password: str,
    admin_group: str,
    editor_group: str,
    verbose: bool,
    skip_deactivate: bool,
    dry_run: bool
) -> Callable[[FsiRequest, FsiApp], None]:
    r""" Updates the list of users/course attendees by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:

    .. code-block:: bash

        onegov-fsi --select /fsi/fsi fetch-users \
            --ldap-server 'ldaps://1.2.3.4' \
            --ldap-username 'foo' \
            --ldap-password 'bar' \
            --admin-group 'ou=Admins' \
            --editor-group 'ou=Editors'

    """

    def execute(request: FsiRequest, app: FsiApp) -> None:

        if dry_run and hasattr(app, 'es_orm_events'):
            # disable search indexing during operation
            click.echo('es_orm_events disabled')
            app.es_orm_events.stopped = True

        fetch_users(
            app,
            request.session,
            ldap_server,
            ldap_username,
            ldap_password,
            admin_group,
            editor_group,
            verbose,
            skip_deactivate,
            dry_run
        )

    return execute


def fetch_users(
    app: FsiApp,
    session: Session,
    ldap_server: str,
    ldap_username: str,
    ldap_password: str,
    admin_group: str,
    editor_group: str,
    verbose: bool = False,
    skip_deactivate: bool = False,
    dry_run: bool = False,
    add_attendee: bool = True
) -> None:
    """ Implements the fetch-users cli command. """

    admin_group = admin_group.lower()
    editor_group = editor_group.lower()
    sources = ZugUserSource.factory(verbose=verbose)

    def users(connection: LDAPConnection) -> Iterator[dict[str, Any]]:
        for src in sources:
            for base, search_filter, attrs in src.bases_filters_attributes:
                success = connection.search(
                    base, search_filter, attributes=attrs
                )
                if not success:
                    log.error('Error importing events', exc_info=True)
                    raise RuntimeError(
                        f"Could not query '{base}' "
                        f"with filter '{search_filter}'"
                    )

                yield from src.map_entries(
                    connection.entries,
                    admin_group=admin_group,
                    editor_group=editor_group,
                    base=base,
                    search_filter=search_filter
                )

    def handle_inactive(synced_ids: list[UUID]) -> None:
        inactive = session.query(User).filter(
            and_(
                User.id.notin_(synced_ids),
                or_(
                    User.source == 'ldap',
                    User.role == 'member'
                )
            )
        )
        for ix, user_ in enumerate(inactive):
            if user_.active:
                log.info(f'Deactivating inactive user {user_.username}')
            user_.active = False
            att: CourseAttendee | None = user_.attendee  # type:ignore
            if att:
                att.active = False

            if not dry_run:
                if ix % 200 == 0:
                    app.fts_indexer.process(session)

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()
    count = 0
    synced_users = []
    for ix, data in enumerate(users(client.connection)):

        if data['type'] == 'ldap':
            source = 'ldap'
            source_id = data['source_id']
            force_role = True
        elif data['type'] == 'regular':
            source = None
            source_id = None
            force_role = False
        else:
            log.error('Unknown auth provider', exc_info=False)
            raise NotImplementedError()

        user = ensure_user(
            source=source,
            source_id=source_id,
            session=session,
            username=data['mail'],
            role=data['role'],
            force_role=force_role,
            force_active=True
        )

        synced_users.append(user.id)

        if add_attendee:
            assert hasattr(user, 'attendee')
            if not user.attendee:
                is_editor = user.role == 'editor'
                permissions = is_editor and [external_attendee_org] or None
                user.attendee = CourseAttendee(permissions=permissions)

            user.attendee.first_name = data['first_name']
            user.attendee.last_name = data['last_name']
            user.attendee.organisation = data['organisation']
            user.attendee.source_id = source_id
            user.attendee.active = user.active

        count += 1
        if not dry_run:
            if ix % 200 == 0:
                app.fts_indexer.process(session)

    log.info(f'Synchronized {count} users')

    if not skip_deactivate:
        handle_inactive(synced_users)

    if dry_run:
        transaction.abort()
