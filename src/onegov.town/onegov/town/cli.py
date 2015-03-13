""" Provides commands used to initialize town websites.

Example (adds a Town called ``Govikon`` to the ``towns-govikon`` schema)::

    dsn=postgres://user:password@localhost:5432/database
    onegov-town --dsn $dsn --schema towns-govikon add Govikon

"""

import click
import sys
import transaction

from onegov.core.orm import Base, SessionManager
from onegov.town.model import Town
from onegov.town.initial_content import add_initial_content


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
@click.argument('name')
@click.pass_context
def add(ctx, name):
    """ Adds a town with the given name to the database. """

    session = ctx.obj['session']

    if session.query(Town).first():
        click.secho(
            "The schema {} already contains a town".format(ctx.obj['schema']),
            fg='red'
        )
        sys.exit(1)

    add_initial_content(session, town_name=name)
    transaction.commit()

    click.secho(
        "{} was added to the {} schema".format(name, ctx.obj['schema']),
        fg='green'
    )
