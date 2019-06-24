import click
import sys

from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_password
from onegov.core.csv import CSVFile
from onegov.user import UserCollection, UserGroupCollection
from sqlalchemy import create_engine


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an instance to the database. For example:

        onegov-wtfs --select '/onegov_wtfs/wtfs' add

    """

    def add_instance(request, app):
        app.cache.invalidate()
        app.add_initial_content()
        click.echo("Instance was created successfully")

    return add_instance


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes an instance from the database. For example:

        onegov-wtfs --select '/onegov_wtfs/wtfs' delete

    """

    def delete_instance(request, app):

        confirmation = "Do you really want to DELETE {}?".format(app.schema)

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        assert app.has_database_connection
        assert app.session_manager.is_valid_schema(app.schema)

        dsn = app.session_manager.dsn
        app.session_manager.session().close_all()
        app.session_manager.dispose()

        engine = create_engine(dsn)
        engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
        engine.raw_connection().invalidate()
        engine.dispose()

        click.echo("Instance was deleted successfully")

    return delete_instance


@cli.command(name='import-users', context_settings={'singular': True})
@click.option('--users', type=click.Path(exists=True), required=True)
def import_users(users):
    """ Imports the wtfs users for migration. For example:

        onegov-twfs --select '/onegov_wtfs/wtfs' import-users --users users.csv

    This should be done after importing the towns and other data.

    """

    roles = {
        'Admin': 'admin',
        'Gemeinde Admin': 'editor',
        'Benutzer': 'member',
    }

    csv = CSVFile(open(users, 'rb'), expected_headers=(
        'bfs',
        'gemeindename',
        'name',
        'email',
        'kontakt',
        'rolle'
    ))

    def handle_import(request, app):
        users = UserCollection(request.session)
        groups = UserGroupCollection(request.session).query()
        existing = {name for name, real in users.usernames}

        missing = (r for r in csv if r.email not in existing)

        for record in missing:
            if record.gemeindename:
                group = groups.filter_by(name=record.gemeindename).first()

                if group is None:
                    print(f"Unknown user group: '{record.gemeindename}'")
                    print(f"Please use on of the following:")
                    for g in sorted([g.name for g in groups]):
                        print(f"- {g}")
                    sys.exit(1)
            else:
                group = None

            users.add(
                username=record.email.strip(),
                password=random_password(16),
                role=roles[record.rolle.strip()],
                realname=record.name.strip(),
                group=group,
                data={'contact': record.kontakt.strip() == 'j'})

    return handle_import
