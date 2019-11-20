import click

from onegov.core.cli import command_group
from onegov.user.auth.clients import LDAPClient


cli = command_group()


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

        onegov-fsi --select /onegov_fsi/fsi fetch-users \\
            --ldap-server ldaps://1.2.3.4 \\
            --ldap-username foo \\
            --ldap-password bar \\

    """

    def execute(request, app):
        fetch_users(request.session, ldap_server, ldap_username, ldap_password)

    return execute


def fetch_users(session, ldap_server, ldap_username, ldap_password):
    """ Implements the fetch-users cli command. """

    # connect to the remote
    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()

    raise NotImplementedError()
