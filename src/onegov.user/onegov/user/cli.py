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
import sys
import transaction

from getpass import getpass
from onegov.user import UserCollection
from onegov.core.orm import Base, SessionManager


@click.group()
@click.option('--dsn', help="Postgresql connection string")
@click.option('--schema', help="Schema to use")
@click.pass_context
def cli(ctx, dsn, schema):
    ctx.obj = {}

    mgr = SessionManager(dsn, base=Base)
    mgr.set_current_schema(schema)

    ctx.obj['schema'] = schema
    ctx.obj['session'] = mgr.session()


@cli.command()
@click.argument('role')
@click.argument('username')
@click.option('--password', help="Password to give the user", default=None)
@click.pass_context
def add(ctx, role, username, password):
    """ Adds a user with the given name to the database. """

    session = ctx.obj['session']
    users = UserCollection(session)

    if users.exists(username):
        click.secho("The user {} already exists".format(username), fg='red')
        sys.exit(1)

    password = password or getpass("Enter password: ")

    users.add(username, password, role)
    transaction.commit()

    click.secho("The user {} was added".format(username), fg='green')


@cli.command()
@click.argument('username')
@click.pass_context
def delete(ctx, username):
    """ Removes the given user from the database. """

    session = ctx.obj['session']
    users = UserCollection(session)

    if not users.exists(username):
        click.secho("The user {} does not exist".format(username), fg='red')
        sys.exit(1)

    users.delete(username)
    transaction.commit()

    click.secho("The user {} was deleted".format(username), fg='green')


@cli.command()
@click.argument('username')
@click.pass_context
def exists(ctx, username):
    """ Returns 0 if the user exists, 1 if it doesn't. """

    session = ctx.obj['session']
    users = UserCollection(session)

    if not users.exists(username):
        click.secho("The user {} does not exist".format(username), fg='red')
        sys.exit(1)
    else:
        click.secho("The user {} exists".format(username), fg='green')
        sys.exit(0)


@cli.command(name='change-password')
@click.argument('username')
@click.option('--password', help="Password to use", default=None)
@click.pass_context
def change_password(ctx, username, password):
    """ Changes the password of the given username. """

    session = ctx.obj['session']
    users = UserCollection(session)

    if not users.exists(username):
        click.secho("The user {} does not exist".format(username), fg='red')
        sys.exit(1)

    password = password or getpass("Enter password: ")

    user = users.by_username(username)
    user.password = password

    transaction.commit()

    click.secho("The password for {} was changed".format(username), fg='green')
