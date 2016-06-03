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
from datetime import date, datetime, timedelta
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

    floor_hours = {
        'Amthaus': (8, 24),
        'Löwen': (0, 24),
        'Gemeinschaftszentrum': (8, 24)
    }

    def run_import(request, app):

        # create all resources first, fails if at least one exists already
        resources = ResourceCollection(app.libres_context)
        floors = {f.id: f.floor_name for f in db.records.floors}
        resources_by_room = {}

        for room in db.records.room:
            resource = resources.add(
                title=room.room_name,
                timezone='Europe/Zurich',
                type='room',
                group=floors[room.floor_id],
                definition=form_definition,
                meta={'is_hidden_from_public': True}
            )

            resources_by_room[room.id] = resource

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

        # get the max_date per resource
        max_dates = {}

        for reservation_group in reservations:
            resource_id = resources_by_room[reservation_group.split('-')[0]].id

            if resource_id not in max_dates:
                max_dates[resource_id] = min_date

            for booking in reservations[reservation_group]:
                date = isodate.parse_datetime(booking.hour_end)

                if max_dates[resource_id] < date:
                    max_dates[resource_id] = date

        # create an allocation for all days between min/max date
        for resource in resources_by_room.values():

            # true if the resource does not have any bookings
            if resource.id not in max_dates:
                continue

            start_hour, end_hour = floor_hours[resource.group]
            days = (max_dates[resource.id].date() - min_date.date()).days

            first_day_start = datetime(
                min_date.year, min_date.month, min_date.day,
                start_hour
            )

            first_day_end = datetime(
                min_date.year, min_date.month, min_date.day,
                end_hour - 1, 59, 59, 999999
            )

            whole_day = (start_hour, end_hour) == (0, 24)

            for day in range(0, days + 1):
                start = first_day_start + timedelta(days=day)
                end = first_day_end + timedelta(days=day)

                resource.scheduler.allocate(
                    dates=(start, end),
                    partly_available=True,
                    whole_day=whole_day,
                )

    return run_import
