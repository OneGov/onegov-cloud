import json
from datetime import date, datetime, timezone
import transaction
from sqlalchemy import or_, and_

import click
from sedate import replace_timezone
from sqlalchemy import cast, Date

from onegov.core.cli import command_group
from onegov.fsi import log
from onegov.fsi.ims_import import parse_ims_data, import_ims_data, \
    import_teacher_data, with_open, parse_date, validate_integer, parse_status
from onegov.fsi.models import CourseAttendee, CourseEvent
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user import User
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.provider import ensure_user
from onegov.user.sync import UserSource

cli = command_group()


def do_ims_import(path, request):
    errors, persons, courses, events, possible_ldap_users = parse_ims_data(
        f'{path}/Teilnehmer.txt',
        f'{path}/Ausführungen.txt',
        f'{path}/Kurse.txt',
        f'{path}/Personen.txt'
    )
    statistics = import_ims_data(
        request.session, persons, courses, events, possible_ldap_users)
    for key, val in statistics.items():
        click.secho(f'{key}: {val}')


@cli.command(name='import-ims-data', context_settings={'singular': True})
@click.option('--path', help='Path with pre-named files', required=True)
def import_ims_data_cli(path):

    def execute(request, app):
        do_ims_import(path, request)
    return execute


@cli.command(name='correct-ims-data', context_settings={'singular': True})
@click.option('--path', help='Path Ausführungen.txt', required=False)
def correct_ims_data_cli(path):

    def fix_original_ims_import(request, app):
        # Import of data was done according to timestamps 15.01.2020
        session = request.session

        def delete_events_without_subscriptions(session):
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

        def parse_date_correct(val, default=None):
            if not val:
                return default
            date_ = datetime.strptime(val, '%d/%m/%Y %H:%M:%S')
            return replace_timezone(date_, 'UTC')

        def correct_datetime(dt):
            return datetime(
                dt.year,
                dt.day,
                dt.month,
                dt.hour,
                dt.minute,
                tzinfo=timezone.utc)

        @with_open
        def open_events_file(csvfile, session):
            corrected_event_ids = set()
            control_messages = []
            for line in csvfile.lines:
                date_lacking = not line.kurs_von or not line.kurs_bis
                if date_lacking:
                    continue
                start = parse_date(line.kurs_von)
                correct_start = parse_date_correct(line.kurs_von)
                min_att = validate_integer(line.teilnehmer_min)
                max_att = validate_integer(line.teilnehmer_max)
                buchungsstatus = line.buchungsstatus
                if start == correct_start or \
                        buchungsstatus == 'Keine Buchungen':
                    continue

                events = session.query(CourseEvent).filter_by(
                    start=start,
                    min_attendees=min_att,
                    max_attendees=max_att,
                    status=parse_status(line.status)
                )
                if corrected_event_ids:
                    events = events.filter(
                        CourseEvent.id.notin_(corrected_event_ids)
                    )

                events = events.all()

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
                if start.day < 13 and not start.day == start.month:
                    to_change_ids.add(event.id)
            print(f'To correct by using created date: {len(to_change_ids)}')
            assert len(to_change_ids) == len(corrected_event_ids)

            return corrected_event_ids, control_messages

        # delete old course events
        total, deleted_count = delete_events_without_subscriptions(session)
        session.flush()
        print(f'Deleted course events without subs: {deleted_count}/{total}')
        corrected_ids, ctrl_msgs = open_events_file(path, session)
        session.flush()

        print(f'Corrected course events using '
              f'original file: {len(corrected_ids)}')

        with open('changed_events.log', 'w') as log_file:
            print('\n'.join((str(i) for i in corrected_ids)), file=log_file)

    return fix_original_ims_import


@cli.command(name='import-teacher-data', context_settings={'singular': True})
@click.option('--path', help='Filepath', required=True)
@click.option('--clear', is_flag=True, default=False,
              help='Clear imported data')
def import_teacher_data_cli(path, clear):

    def execute(request, app):
        import_teacher_data(path, request, clear)
    return execute


class FsiUserSource(UserSource):

    default_filter = '(objectClass=*)'
    ldap_mapping = {
        'uid': 'source_id',
        'zgXGivenName': 'first_name',
        'zgXSurname': 'last_name',
        'mail': 'mail',
        'zgXDirektionAbk': 'directorate',
        'zgXAmtAbk': 'agency',
        'zgXAbteilung': 'department',
    }

    @property
    def ldap_attributes(self):
        additional = ['groupMembership']
        if any(('schulnet' in b.lower() for b in self.bases)):
            additional.append('zgXServiceSubscription')
        return [
            *self.ldap_mapping.keys(),
            *additional
        ]

    def user_type_ktzg(self, entry):
        """ KTZG specific user type """
        mail = entry.entry_attributes_as_dict.get('mail')
        mail = mail and mail[0].strip().lower()
        if mail and mail.endswith('@zg.ch'):
            return 'ldap'
        elif self.verbose:
            print(f'No usertype for {mail}')

    def user_type_default(self, entry):
        """For all the schools, we filter by Mail already, but we exclude the
        students. Name specific user_type functions will run first, this is
         a fallback. """
        attrs = entry.entry_attributes_as_dict
        reasons = attrs.get('zgXServiceSubscription', [])
        reasons = [r.lower() for r in reasons]

        if 'student' in reasons:
            if self.verbose:
                print('Skip: no user_type for student')
            return None

        return 'regular'

    def excluded(self, entry):
        """General exclusion pattern for all synced users. """
        data = entry.entry_attributes_as_dict
        mail = data.get('mail')

        if not mail or not mail[0].strip():
            if self.verbose:
                print('Excluded: No Mail')
            return True

        if entry.entry_dn.count(',') <= 1:
            if self.verbose:
                print(f'Excluded entry_dn.count(",") <= 1: {str(mail)}')
            return True

        if 'ou=HRdeleted' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded HRdeleted: {str(mail)}')
            return True

        if 'ou=Other' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded ou=Other: {str(mail)}')
            return True

        if not self.user_type(entry):
            return True

        # call exclude functions specific to the name of the source
        # if there is any, else return False
        return super().excluded(entry)

    def map_entry(self, entry):
        attrs = entry.entry_attributes_as_dict

        user = {
            column: self.scalar(attrs.get(attr))
            for attr, column in self.ldap_mapping.items()
        }

        user['mail'] = user['mail'].lower().strip()
        user['groups'] = set(g.lower() for g in attrs['groupMembership'])
        user['type'] = self.user_type(entry)

        if user['type'] == 'ldap':
            user['organisation'] = ' / '.join(o for o in (
                user['directorate'],
                user['agency'],
                user['department']
            ) if o)
        elif user['type'] == 'regular':
            domain = self.organisation
            assert domain is not None
            user['organisation'] = domain
        else:
            raise NotImplementedError()

        return user

    def complete_entry(self, user, **kwargs):
        if user['type'] == 'ldap':
            if kwargs['admin_group'] in user['groups']:
                user['role'] = 'admin'
            elif kwargs['editor_group'] in user['groups']:
                user['role'] = 'editor'
            else:
                user['role'] = 'member'
        else:
            user['role'] = 'member'
        return user

    def map_entries(self, entries, **kwargs):
        count = 0
        total = 0
        sf = kwargs.pop('search_filter')
        base = kwargs.pop('base')

        for e in entries:
            total += 1
            if self.excluded(e):
                continue

            count += 1
            user = self.complete_entry(self.map_entry(e), **kwargs)

            yield user
        if self.verbose:
            print(f'Base: {base}\t\tFilter: {sf}')
            print(f'- Total: {total}')
            print(f'- Found: {count}')
            print(f'- Excluded: {total - count}')


schools = dict(
    PHZ={
        'default_filter': '(mail=*@phzg.ch)',
        'org': 'DBK / AMH / Pädagogische Hochschule Zug',
        'bases': ['o=KTZG', 'o=Extern']
    },
    ABA={
        'default_filter': '(mail=*@aba-zug.ch)',
        'org': 'VD / ABA',
        'bases': ['ou=aba,ou=SchulNet,o=Extern']
    },
    FMS={
        'default_filter': '(mail=*@fms-zg.ch)',
        'org': 'DBK / AMH / Fachmittelschule Zug',
        'bases': ['ou=fms,ou=SchulNet,o=Extern']
    },
    KBZ={
        'default_filter': '(mail=*@kbz-zug.ch)',
        'org': 'VD / KBZ',
        'bases': ['ou=kbz,ou=SchulNet,o=Extern']
    },
    KSM={
        'default_filter': '(mail=*@ksmenzingen.ch)',
        'org': 'DBK / AMH / Kantonsschule Menzingen',
        'bases': ['ou=ksm,ou=SchulNet,o=Extern']
    },
    KSZ={
        'default_filter': '(mail=*@ksz.ch)',
        'org': 'DBK / AMH / Kantonsschule Zug',
        'bases': ['ou=ksz,ou=SchulNet,o=Extern']
    },
    GIBZ={
        'org': 'VD / GIBZ',
        'bases': ['ou=gibz,ou=SchulNet,o=Extern']
    }
)

fsi_ldap_users = dict(KTZG={'bases': ['ou=Kanton,o=KTZG']})


@cli.command(name='test-ldap')
@click.option('--base', multiple=True)
@click.option('--search-filter', default='')
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
@click.option('--sort-by', required=True, default='mail')
def test_ldap(base, search_filter, ldap_server, ldap_username, ldap_password,
              sort_by):
    """
    Examples:
    Search for an email: (mail=walter.roderer@zg.ch)
    Search for names: (&(zgXGivenName=Vorname)(zgXSurname=Nachname))
    Search for mail ending in: (mail=*@phgz.ch)

    onegov-fsi --select /fsi/zug test-ldap --base 'ou=Kanton,o=KTZG' \
      --ldap-server 'ldaps://.....' \
      --ldap-username 'user' \
      --ldap-password 'xxxx' --search-filter "(mail=*@zg.ch)"

    """

    def sort_func(entry):
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
            print(f'Search not successfull in base {ba}')
            continue
        for ix, entry in enumerate(
                sorted(client.connection.entries, key=sort_func)
        ):
            print(json.dumps(entry.entry_attributes_as_dict, indent=4))
            count += 1
    print(f'Found {count} entries')


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
        ldap_server,
        ldap_username,
        ldap_password,
        admin_group,
        editor_group,
        verbose,
        skip_deactivate,
        dry_run
):
    """ Updates the list of users/course attendees by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:

        onegov-fsi --select /fsi/fsi fetch-users \\
            --ldap-server 'ldaps://1.2.3.4' \\
            --ldap-username 'foo' \\
            --ldap-password 'bar' \\
            --admin-group 'ou=Admins' \\
            --editor-group 'ou=Editors'

    """

    def execute(request, app):

        if dry_run and hasattr(app, 'es_orm_events'):
            # disable search indexing during operation
            print('es_orm_events disabled')
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


def fetch_users(app, session, ldap_server, ldap_username, ldap_password,
                admin_group=None, editor_group=None, verbose=False,
                skip_deactivate=False, dry_run=False):
    """ Implements the fetch-users cli command. """

    admin_group = admin_group.lower()
    editor_group = editor_group.lower()

    sources = [
        *(FsiUserSource(name, verbose=verbose, **entry)
          for name, entry in schools.items()),
        *(FsiUserSource(name, verbose=verbose, **entry)
          for name, entry in fsi_ldap_users.items())
    ]

    def users(connection):
        for src in sources:
            for base, search_filter, attrs in src.bases_filters_attributes:
                success = connection.search(
                    base, search_filter, attributes=attrs
                )
                if not success:
                    log.error("Error importing events", exc_info=True)
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

    def handle_inactive(synced_ids):
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
            if verbose:
                log.info(f'Inactive: {user_.username}')
            user_.active = False
            att = user_.attendee
            if att:
                att.active = False

            if not dry_run:
                if ix % 200 == 0:
                    app.es_indexer.process()

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
            log.error("Unknown auth provider", exc_info=False)
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
                app.es_indexer.process()
    if not skip_deactivate:
        handle_inactive(synced_users)
    if dry_run:
        transaction.abort()
