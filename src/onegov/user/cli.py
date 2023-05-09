""" Provides commands used to manage users. """

import click

from getpass import getpass
from onegov.user import User, UserCollection
from onegov.core.cli import command_group, abort
from onegov.core.crypto import random_password

cli = command_group()


@cli.command(context_settings={'singular': True})
@click.argument('role')
@click.argument('username')
@click.option('--password', default=None,
              help="Password to give the user")
@click.option('--yubikey', default=None,
              help="The yubikey code to use for 2fa")
@click.option('--realname', default=None,
              help="First name and last name, for example 'Jane Doe'")
@click.option('--phone_number', default=None,
              help="Sets the phone number")
@click.option('--no-prompt', default=False,
              help="If no questions should be asked", is_flag=True)
def add(role, username, password, yubikey, no_prompt, realname, phone_number):
    """ Adds a user with the given name to the database. """

    def add_user(request, app):
        users = UserCollection(app.session())

        print("Adding {} to {}".format(username, app.application_id))

        if users.exists(username):
            abort("{} already exists".format(username))

        nonlocal password
        if not password:
            password = random_password(16)
            print()
            print("Using the following random password:")
            click.secho(password, fg='green')
            print()

        nonlocal yubikey
        if not yubikey and not no_prompt:
            yubikey = getpass(
                "Optionally plug in your yubi-key and press the button: "
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
        click.secho("{} was added".format(username), fg='green')

    return add_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def delete(username):
    """ Removes the given user from the database. """

    def delete_user(request, app):
        users = UserCollection(app.session())

        if not users.exists(username):
            abort("{} does not exist".format(username))

        users.delete(username)
        click.secho("{} was deleted".format(username), fg='green')

    return delete_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def exists(username):
    """ Returns 0 if the user exists, 1 if it doesn't. """

    def find_user(request, app):
        users = UserCollection(app.session())

        if not users.exists(username):
            abort("{} does not exist".format(username))
        else:
            click.secho("{} exists".format(username), fg='green')

    return find_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def activate(username):
    """ Activates the given user. """

    def activate_user(request, app):
        user = UserCollection(app.session()).by_username(username)

        if not user:
            abort("{} does not exist".format(username))

        user.active = True
        click.secho("{} was activated".format(username), fg='green')

    return activate_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def deactivate(username):
    """ Deactivates the given user. """

    def deactivate_user(request, app):
        user = UserCollection(app.session()).by_username(username)

        if not user:
            abort("{} does not exist".format(username))

        user.active = False
        user.logout_all_sessions(request.app)
        click.secho("{} was deactivated".format(username), fg='green')

    return deactivate_user


@cli.command(context_settings={'singular': True})
@click.argument('username')
def logout(username):
    """ Logs out the given user on all sessions. """

    def logout_user(request, app):
        user = UserCollection(app.session()).by_username(username)

        if not user:
            abort("{} does not exist".format(username))

        user.logout_all_sessions(request.app)
        click.secho("{} logged out".format(username), fg='green')

    return logout_user


@cli.command(name='logout-all', context_settings={'singular': True})
def logout_all():
    """ Logs out all users on all sessions. """

    def logout_user(request, app):
        for user in UserCollection(app.session()).query():
            count = user.logout_all_sessions(request.app)
            if count:
                click.secho("{} logged out".format(user.username), fg='green')

    return logout_user


@cli.command(context_settings={'singular': True})
@click.option('--active-only', help="Only show active users", is_flag=True)
@click.option('--inactive-only', help="Only show inactive users", is_flag=True)
@click.option('--sources', help="Display sources", is_flag=True, default=False)
def list(active_only, inactive_only, sources):
    """ Lists all users. """

    assert not all((active_only, inactive_only))

    def list_users(request, app):

        users = UserCollection(app.session()).query()
        users = users.with_entities(
            User.username, User.role, User.active, User.source
        )
        users = users.order_by(User.username, User.role)

        for username, role, active, source in users.all():
            if active_only and not active:
                continue

            if inactive_only and active:
                continue

            print(
                '{active} {username} [{role}]{source}'.format(
                    active='✔︎' if active else '✘',
                    username=username,
                    role=role,
                    source=f' {{{source}}}' if sources else ''
                )
            )

    return list_users


@cli.command(name='change-password', context_settings={'singular': True})
@click.argument('username')
@click.option('--password', help="Password to use", default=None)
def change_password(username, password):
    """ Changes the password of the given username. """

    def change(request, app):
        users = UserCollection(app.session())

        if not users.exists(username):
            abort("{} does not exist".format(username))

        nonlocal password
        password = password or getpass("Enter password: ")

        user = users.by_username(username)
        user.password = password
        user.logout_all_sessions(request.app)

        click.secho("{}'s password was changed".format(username), fg='green')

    return change


@cli.command(name='change-yubikey', context_settings={'singular': True})
@click.argument('username')
@click.option('--yubikey', help="Yubikey to use", default=None)
def change_yubikey(username, yubikey):
    """ Changes the yubikey of the given username. """

    def change(request, app):
        users = UserCollection(app.session())

        if not users.exists(username):
            abort("{} does not exist".format(username))

        nonlocal yubikey
        yubikey = (yubikey or getpass("Enter yubikey: ")).strip()[:12]
        yubikey = yubikey.strip()

        user = users.by_username(username)

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


@cli.command(name='transfer-yubikey', context_settings={'singular': True})
@click.argument('source')
@click.argument('target')
def transfer_yubikey(source, target):
    """ Transfers the Yubikey from one user to another. """

    def transfer(request, app):
        users = UserCollection(app.session())

        if not users.exists(source):
            abort("{} does not exist".format(source))
        if not users.exists(target):
            abort("{} does not exist".format(target))

        source_user = users.by_username(source)
        target_user = users.by_username(target)

        if not source_user.second_factor:
            abort("{} is not linked to a yubikey".format(source))
        if target_user.second_factor:
            abort("{} is already linked to a yubikey".format(target))

        target_user.second_factor = source_user.second_factor
        source_user.second_factor = None

        target_user.logout_all_sessions(request.app)
        source_user.logout_all_sessions(request.app)

        click.secho(
            "yubikey was transferred from {} to {}".format(source, target),
            fg='green'
        )

    return transfer


@cli.command(name='change-role', context_settings={'singular': True})
@click.argument('username')
@click.argument('role')
def change_role(username, role):
    """ Changes the role of the given username. """

    def change(request, app):
        users = UserCollection(app.session())

        if not users.exists(username):
            abort("{} does not exist".format(username))

        user = users.by_username(username)
        user.role = role
        user.logout_all_sessions(request.app)

        click.secho("{}'s role was changed".format(username), fg='green')

    return change


@cli.command(name='list-sessions', context_settings={'singular': True})
def list_sessions():
    """ Lists all sessions of all users. """

    def list_sessions(request, app):
        for user in UserCollection(app.session()).query():
            if user.sessions:
                click.secho('{}'.format(user.username), fg='yellow')
                for session in user.sessions.values():
                    session = session or {}
                    print('{} [{}] "{}"'.format(
                        session.get('address', '?'),
                        session.get('timestamp', '?'),
                        session.get('agent', '?'),
                    ))

    return list_sessions
