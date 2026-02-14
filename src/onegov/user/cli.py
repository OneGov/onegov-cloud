""" Provides commands used to manage users. """
from __future__ import annotations

import click
import phonenumbers
import pyotp

from getpass import getpass
from onegov.user import User, UserCollection
from onegov.core.cli import command_group, abort
from onegov.core.crypto import random_password


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest


cli = command_group()


@cli.command(context_settings={'singular': True})
@click.argument('role')
@click.argument('username')
@click.option('--password', default=None,
              help='Password to give the user')
@click.option('--yubikey', default=None,
              help='The yubikey code to use for 2fa')
@click.option('--realname', default=None,
              help="First name and last name, for example 'Jane Doe'")
@click.option('--phone_number', default=None,
              help='Sets the phone number')
@click.option('--no-prompt', default=False,
              help='If no questions should be asked', is_flag=True)
def add(
    role: str,
    username: str,
    password: str | None,
    yubikey: str | None,
    no_prompt: bool,
    realname: str | None,
    phone_number: str | None
) -> Callable[[CoreRequest, Framework], None]:
    """ Adds a user with the given name to the database. """

    def add_user(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        click.echo('Adding {} to {}'.format(username, app.application_id))

        if users.exists(username):
            abort('{} already exists'.format(username))

        if not hasattr(app.settings.roles, role):
            abort(f'Invalid role "{role}" specified')

        nonlocal password
        if not password:
            password = random_password(16)
            click.echo()
            click.echo('Using the following random password:')
            click.secho(password, fg='green')
            click.echo()

        nonlocal yubikey
        if not yubikey and not no_prompt:
            yubikey = getpass(
                'Optionally plug in your yubi-key and press the button: '
            )

            yubikey = yubikey.strip()

        if yubikey:
            second_factor = {
                'type': 'yubikey',
                'data': yubikey[:12]
            }
        else:
            second_factor = None

        users.add(username, password, role, second_factor=second_factor,
                  phone_number=phone_number, realname=realname)
        click.secho('{} was added'.format(username), fg='green')

    return add_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def delete(username: str) -> Callable[[CoreRequest, Framework], None]:
    """ Removes the given user from the database. """

    def delete_user(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        if not users.exists(username):
            abort('{} does not exist'.format(username))

        users.delete(username)
        click.secho('{} was deleted'.format(username), fg='green')

    return delete_user


@cli.command(context_settings={
    'default_selector': '*',
    'skip_search_indexing': True
})
@click.argument('username')
@click.option('-r', '--recursive', is_flag=True, default=False)
def exists(
    username: str,
    recursive: bool
) -> Callable[[CoreRequest, Framework], None]:
    """ Returns 0 if the user exists, 1 if it doesn't when recursive equals
    to False. If the recursive flag is set, it will loop over all schemas
    and print the result for each schema without return value."""

    def find_user(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        if users.exists(username):
            click.secho(f'{app.schema} {username} exists', fg='green')
        else:
            if recursive:
                click.secho(f'{app.schema} {username} does not exist',
                            fg='yellow')
            else:
                abort(f'{app.schema} {username} does not exist')

    return find_user


@cli.command(context_settings={'singular': True, 'skip_search_indexing': True})
@click.argument('username')
def activate(username: str) -> Callable[[CoreRequest, Framework], None]:
    """ Activates the given user. """

    def activate_user(request: CoreRequest, app: Framework) -> None:
        user = UserCollection(app.session()).by_username(username)

        if user is None:
            abort('{} does not exist'.format(username))

        user.active = True
        click.secho('{} was activated'.format(username), fg='green')

    return activate_user


@cli.command(context_settings={'singular': True, 'skip_search_indexing': True})
@click.argument('username')
def deactivate(username: str) -> Callable[[CoreRequest, Framework], None]:
    """ Deactivates the given user. """

    def deactivate_user(request: CoreRequest, app: Framework) -> None:
        user = UserCollection(app.session()).by_username(username)

        if not user:
            abort('{} does not exist'.format(username))

        user.active = False
        user.logout_all_sessions(request.app)
        click.secho('{} was deactivated'.format(username), fg='green')

    return deactivate_user


@cli.command(context_settings={'singular': True, 'skip_search_indexing': True})
@click.argument('username')
def logout(username: str) -> Callable[[CoreRequest, Framework], None]:
    """ Logs out the given user on all sessions. """

    def logout_user(request: CoreRequest, app: Framework) -> None:
        user = UserCollection(app.session()).by_username(username)

        if not user:
            abort('{} does not exist'.format(username))

        user.logout_all_sessions(request.app)
        click.secho('{} logged out'.format(username), fg='green')

    return logout_user


@cli.command(name='logout-all', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
def logout_all() -> Callable[[CoreRequest, Framework], None]:
    """ Logs out all users on all sessions. """

    def logout_user(request: CoreRequest, app: Framework) -> None:
        for user in UserCollection(app.session()).query():
            count = user.logout_all_sessions(request.app)
            if count:
                click.secho('{} logged out'.format(user.username), fg='green')

    return logout_user


@cli.command(context_settings={
    'default_selector': '*',
    'skip_search_indexing': True
})
@click.option('--active-only', help='Only show active users', is_flag=True)
@click.option('--inactive-only', help='Only show inactive users', is_flag=True)
@click.option('--sources', help='Display sources', is_flag=True, default=False)
def list(
    active_only: bool,
    inactive_only: bool,
    sources: bool
) -> Callable[[CoreRequest, Framework], None]:
    """ Lists all users. """

    assert not all((active_only, inactive_only))

    def list_users(request: CoreRequest, app: Framework) -> None:

        users = UserCollection(app.session()).query().with_entities(
            User.username, User.role, User.active, User.source
        )
        users = users.order_by(User.username, User.role)

        click.echo(f'{app.schema}:')
        for username, role, active, source in users.tuples():
            if active_only and not active:
                continue

            if inactive_only and active:
                continue

            click.echo(
                '  {active} {username} [{role}]{source}'.format(
                    active='✔︎' if active else '✘',
                    username=username,
                    role=role,
                    source=f' {{{source}}}' if sources else ''
                )
            )

    return list_users


@cli.command(name='change-password', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('username')
@click.option('--password', help='Password to use', default=None)
def change_password(
    username: str,
    password: str | None
) -> Callable[[CoreRequest, Framework], None]:
    """ Changes the password of the given username. """

    def change(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        user = users.by_username(username)
        if user is None:
            abort('{} does not exist'.format(username))

        nonlocal password
        password = password or getpass('Enter password: ')

        user.password = password
        user.logout_all_sessions(request.app)

        click.secho("{}'s password was changed".format(username), fg='green')

    return change


@cli.command(name='change-yubikey', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('username')
@click.option('--yubikey', help='Yubikey to use', default=None)
def change_yubikey(
    username: str,
    yubikey: str | None
) -> Callable[[CoreRequest, Framework], None]:
    """ Changes the yubikey of the given username. """

    def change(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        user = users.by_username(username)
        if user is None:
            abort('{} does not exist'.format(username))

        nonlocal yubikey
        yubikey = (yubikey or getpass('Enter yubikey: ')).strip()[:12]
        yubikey = yubikey.strip()

        if yubikey:
            user.second_factor = {
                'type': 'yubikey',
                'data': yubikey
            }
        else:
            user.second_factor = None
        user.logout_all_sessions(request.app)

        click.secho("{}'s yubikey was changed".format(username), fg='green')

    return change


@cli.command(name='change-mtan', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('username')
@click.option('--phone-number', help='Phone number to use', default=None)
def change_mtan(
    username: str,
    phone_number: str | None
) -> Callable[[CoreRequest, Framework], None]:
    """ Changes the yubikey of the given username. """

    def change(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        user = users.by_username(username)
        if user is None:
            abort(f'{username} does not exist')

        nonlocal phone_number
        phone_number = (phone_number or getpass('Enter phone number: '))
        phone_number = phone_number.strip()

        if phone_number:
            try:
                number_obj = phonenumbers.parse(phone_number, 'CH')
            except Exception:
                abort(f'Failed to parse {phone_number} as a phone number')

            if not (
                phonenumbers.is_valid_number(number_obj)
                and phonenumbers.is_possible_number(number_obj)
            ):
                abort(f'{phone_number} is not a valid phone number')

            phone_number = phonenumbers.format_number(
                number_obj,
                phonenumbers.PhoneNumberFormat.E164
            )
            user.second_factor = {
                'type': 'mtan',
                'data': phone_number
            }
        else:
            user.second_factor = None
        user.logout_all_sessions(request.app)

        click.secho(f"{username}'s phone number was changed", fg='green')

    return change


@cli.command(name='change-totp', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('username')
@click.option('--secret', help='TOTP secret to use', default=None)
@click.option(
    '--generate',
    help='Generate a new TOTP secret to use',
    is_flag=True,
    default=False
)
def change_totp(
    username: str,
    secret: str | None,
    generate: bool
) -> Callable[[CoreRequest, Framework], None]:
    """ Changes the yubikey of the given username. """

    def change(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        user = users.by_username(username)
        if user is None:
            abort(f'{username} does not exist')

        if generate:
            totp_secret = pyotp.random_base32()
        elif secret is None:
            totp_secret = getpass('Enter secret: ').strip()
        else:
            totp_secret = secret.strip()

        if totp_secret:
            user.second_factor = {
                'type': 'totp',
                'data': totp_secret
            }
        else:
            user.second_factor = None
        user.logout_all_sessions(request.app)

        click.secho(f"{username}'s TOTP secret was changed", fg='green')

        if generate:
            click.echo(f'Generated secret: {totp_secret}')

    return change


@cli.command(name='transfer-yubikey', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('source')
@click.argument('target')
def transfer_yubikey(
    source: str,
    target: str
) -> Callable[[CoreRequest, Framework], None]:
    """ Transfers the Yubikey from one user to another. """

    def transfer(request: CoreRequest, app: Framework) -> None:
        users = UserCollection(app.session())

        source_user = users.by_username(source)
        if source_user is None:
            abort('{} does not exist'.format(source))

        target_user = users.by_username(target)
        if target_user is None:
            abort('{} does not exist'.format(target))

        if not source_user.second_factor:
            abort('{} is not linked to a yubikey'.format(source))
        if target_user.second_factor:
            abort('{} is already linked to a yubikey'.format(target))

        target_user.second_factor = source_user.second_factor
        source_user.second_factor = None

        target_user.logout_all_sessions(request.app)
        source_user.logout_all_sessions(request.app)

        click.secho(
            'yubikey was transferred from {} to {}'.format(source, target),
            fg='green'
        )

    return transfer


@cli.command(name='change-role', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
@click.argument('username')
@click.argument('role')
def change_role(
    username: str,
    role: str
) -> Callable[[CoreRequest, Framework], None]:
    """ Changes the role of the given username. """

    def change(request: CoreRequest, app: Framework) -> None:
        if not hasattr(app.settings.roles, role):
            abort(f'Invalid role "{role}" specified')

        users = UserCollection(app.session())

        user = users.by_username(username)
        if user is None:
            abort('{} does not exist'.format(username))

        user.role = role
        user.logout_all_sessions(request.app)

        click.secho("{}'s role was changed".format(username), fg='green')

    return change


@cli.command(name='list-sessions', context_settings={
    'singular': True,
    'skip_search_indexing': True
})
def list_sessions() -> Callable[[CoreRequest, Framework], None]:
    """ Lists all sessions of all users. """

    def list_sessions(request: CoreRequest, app: Framework) -> None:
        for user in UserCollection(app.session()).query():
            if user.sessions:
                click.secho('{}'.format(user.username), fg='yellow')
                for session in user.sessions.values():
                    session = session or {}  # type:ignore[unreachable]
                    click.echo('{} [{}] "{}"'.format(
                        session.get('address') or '?',
                        session.get('timestamp') or '?',
                        session.get('agent') or '?',
                    ))

    return list_sessions
