import click

from onegov.core.cli import command_group
from onegov.fsi.models import CourseAttendee
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.provider import ensure_user


cli = command_group()


@cli.command(name='fetch-users', context_settings={'singular': True})
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
@click.option('--ldap-base', required=True, default='ou=Kanton,o=KTZG')
def fetch_users_cli(ldap_server, ldap_username, ldap_password, ldap_base):
    """ Updates the list of users/course attendees by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:

        onegov-fsi --select /onegov_fsi/fsi fetch-users \\
            --ldap-server ldaps://1.2.3.4 \\
            --ldap-username foo \\
            --ldap-password bar \\

    """

    def execute(request, app):
        fetch_users(
            request.session,
            ldap_server,
            ldap_username,
            ldap_password,
            ldap_base)

    return execute


def fetch_users(session, ldap_server, ldap_username, ldap_password, ldap_base):
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

    def excluded(entry):
        if entry.entry_dn == ldap_base:
            return True

        if 'ou=HRdeleted' in entry.entry_dn:
            return True

        if 'ou=Other' in entry.entry_dn:
            return True

        if not entry.entry_attributes_as_dict.get('mail'):
            return True

    def scalar(value):
        if value and isinstance(value, list):
            return value[0]

        return value or ''

    def as_user(entry):
        attrs = entry.entry_attributes_as_dict

        user = {
            column: scalar(attrs.get(attr))
            for attr, column in mapping.items()
        }

        user['groups'] = set(g.lower() for g in attrs['groupMembership'])

        return user

    def users(connection):
        attributes = [*mapping.keys(), 'groupMembership']

        success = connection.search(
            ldap_base, "(objectClass=*)", attributes=attributes)

        if not success:
            return

        for e in connection.entries:

            if excluded(e):
                continue

            user = as_user(e)

            if admin_group in user['groups']:
                user['role'] = 'admin'
            elif editor_group in user['groups']:
                user['role'] = 'editor'
            else:
                user['role'] = 'member'

            yield user

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()

    for data in users(client.connection):
        user = ensure_user(
            source='ldap',
            source_id=data['source_id'],
            session=session,
            username=data['mail'],
            role=data['role'])

        if not user.attendee:
            user.attendee = CourseAttendee()

        user.attendee.first_name = data['first_name']
        user.attendee.last_name = data['last_name']
        user.attendee._email = data['mail']
        user.attendee.organisation = ' / '.join(o for o in (
            data['directorate'],
            data['agency'],
            data['department']
        ) if o)
