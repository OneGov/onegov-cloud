import click

from cached_property import cached_property
from io import BytesIO
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import random_password
from onegov.core.csv import CSVFile, convert_xls_to_csv
from onegov.core.utils import Bunch
from onegov.user import UserCollection, UserGroupCollection
from pathlib import Path
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


@cli.command(name='import', context_settings={'singular': True})
@click.option('--path', type=click.Path(exists=True), required=True)
def import_users(path):
    """ Imports the wtfs live data from the legacy system. """

    roles = {
        'Admin': 'admin',
        'Gemeinde Admin': 'editor',
        'Benutzer': 'member',
    }

    path = Path(path)

    def slurp(file):
        return BytesIO(file.read())

    def as_csv(path):
        if path.name.endswith('xlsx'):
            adapt = convert_xls_to_csv
        else:
            adapt = slurp

        with open(path, 'rb') as f:
            return CSVFile(adapt(f))

    def load_files(path):

        prefix = 'tx_winscan_domain_model'

        files = Bunch()
        files.users = as_csv(path / 'users.xlsx')
        files.bill = as_csv(path / f'{prefix}_bill.csv')
        files.date = as_csv(path / f'{prefix}_date.csv')
        files.paymenttype = as_csv(path / f'{prefix}_paymenttype.csv')
        files.township = as_csv(path / f'{prefix}_township.csv')
        files.transportorder = as_csv(path / f'{prefix}_transportorder.csv')
        files.transporttype = as_csv(path / f'{prefix}_transporttype.csv')

        return files

    files = load_files(path)

    class Context(object):

        def __init__(self, session):
            self.session = session

        @cached_property
        def users(self):
            return UserCollection(self.session)

        @cached_property
        def groups(self):
            return UserGroupCollection(self.session, type='wtfs')

    def town_name(town):
        name = town.name.rstrip(' 123456789')
        name = f'{name} ({town.bfs_nr})'

    def town_payment_type(town):
        return town.payment_type == '1' and 'normal' or 'spezial'

    def handle_import(request, app):
        context = Context(request.session)
        created = Bunch(towns={}, users=[])

        print("* Importing towns")
        for town in files.township:

            if town.deleted == '1':
                continue

            # towns double as user groups
            group = context.groups.add(
                name=town.name,
                bfs_number=town.bfs_nr,
                address_supplement=town.address_extension,
                gpn_number=town.gp_nr,
                payment_type=town_payment_type(town),
                type='wtfs')

            assert group.bfs_number not in created.towns
            created.towns[group.bfs_number] = group

        print("* Importing users")
        for user in files.users:

            created.users.append(context.users.add(
                username=user.email,
                password=random_password(16),
                role=roles[user.rolle],
                realname=user.name,
                group=user.bfs and created.towns[user.bfs],
                data={'contact': user.kontakt == 'j'}))

    return handle_import
