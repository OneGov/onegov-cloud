import click

from onegov.core.cache import lru_cache
from onegov.core.cli import command_group
from onegov.fsi import log
from onegov.fsi.ims_import import parse_ims_data, import_ims_data, \
    import_teacher_data
from onegov.fsi.models import CourseAttendee
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
        fetch_users(
            app,
            request.session,
            ldap_server,
            ldap_username,
            ldap_password)

    return execute


def fetch_users(app, session, ldap_server, ldap_username, ldap_password):
    """ Implements the fetch-users cli command. """

    admin_group = 'cn=acc_onegovcloud_admin,ou=kursverwaltung,o=appl'
    editor_group = 'cn=acc_onegovcloud_edit,ou=kursverwaltung,o=appl'

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
