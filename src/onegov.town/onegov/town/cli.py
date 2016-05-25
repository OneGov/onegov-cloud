""" Provides commands used to initialize town websites.

Example (adds a Town called ``Govikon`` to the ``towns-govikon`` schema)::

    dsn=postgres://user:password@localhost:5432/database
    onegov-town --dsn $dsn --schema towns-govikon add Govikon

"""

import click

from onegov.core.cli import command_group, pass_group_context, abort
from onegov.town.models import Town
from onegov.town.initial_content import add_initial_content
from sqlalchemy import create_engine


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@click.argument('name')
@pass_group_context
def add(group_context, name):
    """ Adds a town with the given name to the database. For example:

        onegov-town /onegov_town/newyork add "New York"

    """

    def add_town(request, app):

        if app.session().query(Town).first():
            abort("{} already contains a town".format(group_context.selector))

        add_initial_content(app.libres_registry, app.session_manager, name)

        click.echo("{} was created successfully".format(name))

    return add_town


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes a single town matching the selector.

    Selector matching multiple towns are disabled for saftey reasons.

    """

    def delete_town(request, app):

        town = app.town.name
        confirmation = "Do you really want to DELETE {}?".format(town)

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        if app.has_filestorage:
            click.echo("Removing File Storage")

            for item in app.filestorage.listdir():
                if app.filestorage.isdir(item):
                    app.filestorage.removedir(item, recursive=True, force=True)
                else:
                    app.filestorage.remove(item)

        if app.has_database_connection:
            click.echo("Dropping Database Schema")

            assert app.session_manager.is_valid_schema(app.schema)

            dsn = app.session_manager.dsn
            app.session_manager.session().close_all()
            app.session_manager.dispose()

            engine = create_engine(dsn)
            engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
            engine.raw_connection().invalidate()
            engine.dispose()

        click.echo("{} was deleted successfully".format(town))

    return delete_town
