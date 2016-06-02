""" Provides commands used to initialize town websites.

Example (adds a Town called ``Govikon`` to the ``towns-govikon`` schema)::

    dsn=postgres://user:password@localhost:5432/database
    onegov-town --dsn $dsn --schema towns-govikon add Govikon

"""

import click
import isodate
import shutil
import textwrap

from collections import defaultdict
from datetime import date, datetime
from onegov.core.cli import command_group, pass_group_context, abort
from onegov.libres import ResourceCollection
from onegov.town.formats import DigirezDB
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


@cli.command(name='import-digirez', context_settings={'singular': True})
@click.argument('accessdb', type=click.Path(exists=True, resolve_path=True))
@click.option('--min-date', default=None,
              help="Min date in the form '2016-12-31'")
def import_digirez(accessdb, min_date):
    """ Imports a Digirez reservation database into onegov.town.

    Example:

        onegov-town --select '/towns/govikon' import-digirez room_booking.mdb

    """

    if not shutil.which('mdb-export'):
        abort("Could not find 'mdb-export', please install mdbtools!")

    min_date = min_date and isodate.parse_date(min_date) or date.today()
    min_date = datetime(min_date.year, min_date.month, min_date.day)

    db = DigirezDB(accessdb)
    db.open()

    # XXX this is currently specific to what Gemeinde Rüti has, we could put
    # this into an external file however.
    form_definition = textwrap.dedent("""
        Name *= ___
        Telefon *=___
        Zweck *= ___
        Einrichtungen =
            [ ] Konzertbestuhlung
            [ ] Bankettbestuhlung
            [ ] Flipchart
            [ ] Hellraumprojektor
            [ ] Kinoleinwand (Saal)
            [ ] Mobile Leinwand
            [ ] Lautsprecheranlage
            [ ] Podestelemente
            [ ] Flügel (Saal)
            [ ] Getränke
            [ ] Küche (Saal)
            [ ] Office (Keller)
        Bemerkungen = ...
    """)

    def run_import(request, app):

        # create all resources first, fails if at least one exists already
        resources = ResourceCollection(app.libres_context)
        floors = {f.id: f.floor_name for f in db.records.floors}
        resource_ids_by_room = {}

        for room in db.records.room:
            resource = resources.add(
                title=room.room_name,
                timezone='Europe/Zurich',
                type='room',
                group=floors[room.floor_id],
                definition=form_definition
            )

            resource_ids_by_room[room.id] = resource.id

        # get a list of all relevant reservations
        relevant_bookings = (
            b for b in db.records.room_booking
            if isodate.parse_datetime(b.hour_end) > min_date
        )

        # group by room id in addition to the multi_id, as digirez supports
        # reservations which span multiple rooms
        reservations = defaultdict(list)

        for booking in relevant_bookings:
            group = '-'.join((booking.room_id, booking.multi_id))
            reservations[group].append(booking)

        # create the reservations
        pass

    return run_import
