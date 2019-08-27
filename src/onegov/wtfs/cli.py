import click
import sedate

from cached_property import cached_property
from datetime import datetime
from io import BytesIO
from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.crypto import hash_password, random_password
from onegov.core.csv import CSVFile, convert_xls_to_csv
from onegov.core.utils import Bunch
from onegov.user import User, UserGroupCollection
from onegov.wtfs.models import PickupDate, ScanJob
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

    # we use a single random password for all accounts, which is known to
    # nobody (users are meant to request a new password after import)
    #
    # this speeds up the user import by an order of magnitude
    #
    # don't blindly copy this!
    password_hash = hash_password(random_password(128))

    roles = {
        'Admin': 'admin',
        'Gemeinde Admin': 'editor',
        'Benutzer': 'member',
    }

    types = {
        '1': 'normal',
        '2': 'express',
    }

    path = Path(path)

    def fix(string):
        # one of the CSV files has a line that seems to elude our parser,
        # so we just fix it up
        return string.replace(
            b'""violett; Def. an Scan-Center""',
            b"'violett; Def. an Scan-Center'"
        )

    def slurp(file):
        return BytesIO(fix(file.read()))

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
        files.users = as_csv(path / 'User_Scanauftrag_neu.xlsx')
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
        def groups(self):
            return UserGroupCollection(self.session, type='wtfs')

    def town_name(town):
        name = town.name.rstrip(' 123456789')
        name = f'{name} ({town.bfs_nr})'

    def town_payment_type(town):
        return town.payment_type == '1' and 'normal' or 'spezial'

    def parse_datetime(dt):
        d = datetime.utcfromtimestamp(int(dt))
        d = sedate.replace_timezone(d, 'UTC')
        d = sedate.to_timezone(d, 'Europe/Zurich')

        return d

    def handle_import(request, app):
        context = Context(request.session)
        created = Bunch(towns={}, users=[], dates=[], jobs=[])
        townids = {}
        deleted = set()

        for record in files.township:

            if record.deleted == '1':
                deleted.add(record.uid)
                continue

            # towns double as user groups
            group = context.groups.add(
                name=record.name,
                bfs_number=record.bfs_nr,
                address_supplement=record.address_extension,
                gpn_number=record.gp_nr.isdigit() and int(record.gp_nr),
                payment_type=town_payment_type(record),
                type='wtfs')

            townids[record.uid] = record.bfs_nr

            assert group.bfs_number not in created.towns
            created.towns[group.bfs_number] = group

        print(f"✓ Imported {len(created.towns)} towns")

        for record in files.users:

            user = User(
                username=record.email,
                role=roles[record.rolle],
                realname=record.name,
                active=True,
                second_factor=None,
                signup_token=None,
                password_hash=password_hash,
                group_id=record.bfs and created.towns[record.bfs].id or None,
                data={'contact': record.kontakt == 'j'})

            context.session.add(user)
            created.users.append(user)

        print(f"✓ Imported {len(created.users)} users")

        for record in files.date:

            if record.township in deleted:
                continue

            if record.deleted == '1' or record.township == '0':
                continue

            dt = parse_datetime(record.date).date()

            pickup_date = PickupDate(
                date=dt,
                municipality_id=created.towns[townids[record.township]].id)

            context.session.add(pickup_date)
            created.dates.append(pickup_date)

        print(f"✓ Imported {len(created.dates)} dates")

        for record in files.transportorder:
            dispatch_date = parse_datetime(record.distribution_date).date()
            return_date = parse_datetime(record.return_date).date()

            if record.deleted == '1' or record.township == '0':
                continue

            if record.township in deleted:
                continue

            job = ScanJob(
                municipality_id=created.towns[townids[record.township]].id,
                type=types[record.transport_type],
                delivery_number=record.delivery_bill_number,

                # dispatch (in)
                dispatch_date=dispatch_date,
                dispatch_note=record.comment_delivery,
                dispatch_boxes=int(record.box_in),
                dispatch_tax_forms_current_year=int(
                    record.tax_current_year_in),
                dispatch_tax_forms_last_year=int(
                    record.tax_last_year_in),
                dispatch_tax_forms_older=int(
                    record.tax_old_in),
                dispatch_single_documents=int(
                    record.single_voucher_in),

                # targets (ribbon stands for "Bändliweg" I think)
                dispatch_cantonal_tax_office=int(
                    record.ribbon_out),
                dispatch_cantonal_scan_center=int(
                    record.cantonal_scan_center),

                # return (out)
                return_date=return_date,
                return_note=record.comment_handover,
                return_boxes=record.box_out,
                return_tax_forms_current_year=int(
                    record.tax_current_year_out),
                return_tax_forms_last_year=int(
                    record.tax_last_year_out),
                return_tax_forms_older=int(
                    record.tax_old_out),
                return_single_documents=int(
                    record.single_voucher_out),
                return_unscanned_tax_forms_current_year=int(
                    record.not_scanned_current_year),
                return_unscanned_tax_forms_last_year=int(
                    record.not_scanned_last_year),
                return_unscanned_tax_forms_older=int(
                    record.not_scanned_old),
                return_unscanned_single_documents=int(
                    record.not_scanned_voucher)
            )

            context.session.add(job)
            created.jobs.append(job)

        print(f"✓ Imported {len(created.jobs)} jobs")

    return handle_import
