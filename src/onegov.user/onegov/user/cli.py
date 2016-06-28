""" Provides commands used to manage users.

Examples:

To add a user called ``admin@example.org`` to the ``towns-govikon`` schema,
with the role 'admin'::

    dsn=postgres://user:password@localhost:5432/database
    schema=towns-govikon
    onegov-user --dsn $dsn --schema $schema add admin admin@example.org

This command will ask for a password if none was provided with ``--password``.

To delete a user::

    dsn=postgres://user:password@localhost:5432/database
    schema=towns-govikon
    onegov-user --dsn $dsn --schema $schema delete admin@example.org

To check if a user exists::

    dsn=postgres://user:password@localhost:5432/database
    schema=towns-govikon
    onegov-user --dsn $dsn --schema $schema exists admin@example.org

To change a users password::

    dsn=postgres://user:password@localhost:5432/database
    schema=towns-govikon
    onegov-user --dsn $dsn --schema $schema change-password admin@example.org

This command will also ask for a password if none was provided with
``--password``.

"""

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
@click.option('--no-prompt', default=False,
              help="If no questions should be asked", is_flag=True)
def add(role, username, password, yubikey, no_prompt):
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

        users.add(username, password, role, second_factor=second_factor)
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
        click.secho("{} was deactivated".format(username), fg='green')

    return deactivate_user


@cli.command(context_settings={'singular': True})
@click.option('--active-only', help="Only show active users", is_flag=True)
@click.option('--inactive-only', help="Only show inactive users", is_flag=True)
def list(active_only, inactive_only):
    """ Lists all users. """

    assert not all((active_only, inactive_only))

    def list_users(request, app):

        template = '{active} {username} [{role}]'

        users = UserCollection(app.session()).query()
        users = users.with_entities(User.username, User.role, User.active)
        users = users.order_by(User.username, User.role)

        for username, role, active in users.all():
            if active_only and not active:
                continue

            if inactive_only and active:
                continue

            print(template.format(
                active=active and '✔︎' or '✘',
                username=username,
                role=role
            ))

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

        user = users.by_username(username)
        user.second_factor = {
            'type': 'yubikey',
            'data': yubikey
        }

        click.secho("{}'s yubikey was changed".format(username), fg='green')

    return change
