from datetime import date, datetime, timezone

import click
from sedate import replace_timezone
from sqlalchemy import cast, Date

from onegov.core.cache import lru_cache
from onegov.core.cli import command_group
from onegov.fsi import log
from onegov.fsi.ims_import import parse_ims_data, import_ims_data, \
    import_teacher_data, with_open, parse_date, validate_integer, parse_status
from onegov.fsi.models import CourseAttendee, CourseEvent
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.provider import ensure_user


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


schools = {
    '@gibz.ch': 'VD / GIBZ',
    '@kbz-zug.ch': 'VD / KBZ',
    '@aba-zug.ch': 'VD / ABA',
    '@ksmenzingen.ch': 'DBK / AMH / Kantonsschule Menzingen',
    '@ksz.ch': 'DBK / AMH / Kantonsschule Zug',
    '@phzg.ch': 'DBK / AMH / Pädagogische Hochschule Zug',
    '@fms-zg.ch': 'DBK / AMH / Fachmittelschule Zug',
}


@cli.command(name='fetch-users', context_settings={'singular': True})
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
def fetch_users_cli(ldap_server, ldap_username, ldap_password):
    """ Updates the list of users/course attendees by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:

        onegov-fsi --select /fsi/fsi fetch-users \\
            --ldap-server 'ldaps://1.2.3.4' \\
            --ldap-username 'foo' \\
            --ldap-password 'bar' \\

    """

    def execute(request, app):
        admin_group = 'cn=OneGovCloud_Admin,ou=kursverwaltung,o=appl'
        editor_group = 'cn=OneGovCloud_edit,ou=kursverwaltung,o=appl'
        fetch_users(
            app,
            request.session,
            ldap_server,
            ldap_username,
            ldap_password,
            admin_group,
            editor_group
        )

    return execute


def fetch_users(app, session, ldap_server, ldap_username, ldap_password,
                admin_group=None, editor_group=None):
    """ Implements the fetch-users cli command. """

    mapping = {
        'uid': 'source_id',
        'zgXGivenName': 'first_name',
        'zgXSurname': 'last_name',
        'mail': 'mail',
        'zgXDirektionAbk': 'directorate',
        'zgXAmtAbk': 'agency',
        'zgXAbteilung': 'department',
    }

    @lru_cache(maxsize=1)
    def match_school_domain(mail):
        for domain in schools:
            if mail.endswith(domain):
                return domain

        return None

    def user_type(mail):

        if match_school_domain(mail):
            return 'regular'

        if mail.endswith('zg.ch'):
            return 'ldap'

        return None

    def excluded(entry):
        if entry.entry_dn.count(',') <= 1:
            return True

        if 'ou=HRdeleted' in entry.entry_dn:
            return True

        if 'ou=Other' in entry.entry_dn:
            return True

        if not entry.entry_attributes_as_dict.get('mail'):
            return True

        if not user_type(entry.entry_attributes_as_dict['mail'][0]):
            return True

    def scalar(value):
        if value and isinstance(value, list):
            return value[0]

        return value or ''

    def map_entry(entry):
        attrs = entry.entry_attributes_as_dict

        user = {
            column: scalar(attrs.get(attr))
            for attr, column in mapping.items()
        }

        user['mail'] = user['mail'].lower().strip()
        user['groups'] = set(g.lower() for g in attrs['groupMembership'])
        user['type'] = user_type(user['mail'])

        if user['type'] == 'ldap':
            user['organisation'] = ' / '.join(o for o in (
                user['directorate'],
                user['agency'],
                user['department']
            ) if o)
        elif user['type'] == 'regular':
            domain = match_school_domain(user['mail'])
            assert domain is not None
            user['organisation'] = schools[domain]
        else:
            raise NotImplementedError()

        return user

    def map_entries(entries):
        for e in entries:

            if excluded(e):
                continue

            user = map_entry(e)

            if user['type'] == 'ldap':
                if admin_group in user['groups']:
                    user['role'] = 'admin'
                elif editor_group in user['groups']:
                    user['role'] = 'editor'
                else:
                    user['role'] = 'member'
            else:
                user['role'] = 'member'

            yield user

    def users(connection):
        attributes = [*mapping.keys(), 'groupMembership']
        bases = ('ou=SchulNet,o=Extern', 'ou=Kanton,o=KTZG')

        for base in bases:
            success = connection.search(
                base, "(objectClass=*)", attributes=attributes)

            if not success:
                log.error("Error importing events", exc_info=True)
                raise RuntimeError(f"Could not query '{base}'")

            yield from map_entries(connection.entries)

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()
    count = 0
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
            force_role=force_role)

        if not user.attendee:
            is_editor = user.role == 'editor'
            permissions = is_editor and external_attendee_org or None
            user.attendee = CourseAttendee(permissions=permissions)

        user.attendee.first_name = data['first_name']
        user.attendee.last_name = data['last_name']
        user.attendee.organisation = data['organisation']
        user.attendee.source_id = source_id

        count += 1

        if ix % 200 == 0:
            app.es_indexer.process()
    # log.info(f'LDAP users imported (#{count})')
