""" Provides commands used to initialize org websites. """

import click
import html
import isodate
import re
import shutil
import textwrap

from collections import defaultdict
from datetime import date, datetime, timedelta
from libres.modules.errors import InvalidEmailAddress, AlreadyReservedError
from onegov.core.cli import command_group, pass_group_context, abort
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.org.formats import DigirezDB
from onegov.org.models import Organisation
from onegov.ticket import TicketCollection
from onegov.user import UserCollection, User
from sqlalchemy import create_engine
from uuid import uuid4


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@click.argument('name')
@pass_group_context
def add(group_context, name):
    """ Adds an org with the given name to the database. For example:

        onegov-org --select '/onegov_org/evilcorp' add "Evilcorp"

    """

    def add_org(request, app):

        if app.session().query(Organisation).first():
            abort("{} already contains an organisation".format(
                group_context.selector))

        app.settings.org.create_new_organisation(app, name)

        click.echo("{} was created successfully".format(name))

    return add_org


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes a single organisation matching the selector.

    Selectors matching multiple organisations are disabled for saftey reasons.

    """

    def delete_org(request, app):

        org = app.org.name
        confirmation = "Do you really want to DELETE {}?".format(org)

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

        click.echo("{} was deleted successfully".format(org))

    return delete_org


@cli.command(name='import-digirez', context_settings={'singular': True})
@click.argument('accessdb', type=click.Path(exists=True, resolve_path=True))
@click.option('--min-date', default=None,
              help="Min date in the form '2016-12-31'")
@click.option('--ignore-booking-conflicts', default=False, is_flag=True,
              help="Ignore booking conflicts (TESTING ONlY)")
def import_digirez(accessdb, min_date, ignore_booking_conflicts):
    """ Imports a Digirez reservation database into onegov.org.

    Example:

        onegov-org --select '/orgs/govikon' import-digirez room_booking.mdb

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
        Telefon =___
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

    title_map = {
        'Jugend- raum': 'Jugendraum',
        'Spielgruppen- Raum': 'Spielgruppenraum',
        'Vereins- raum': 'Vereinsraum'
    }

    def get_formdata(member, booking):

        einrichtungen = []

        if booking.kbest == '1':
            einrichtungen.append('Konzertbestuhlung')

        if booking.bbest == '1':
            einrichtungen.append('Bankettbestuhlung')

        if booking.flip == '1':
            einrichtungen.append('Flipchart')

        if booking.ohproj == '1':
            einrichtungen.append('Hellraumprojektor')

        if booking.klw == '1':
            einrichtungen.append('Kinoleinwand (Saal)')

        if booking.mlw == '1':
            einrichtungen.append('Mobile Leinwand')

        if booking.lspr == '1':
            einrichtungen.append('Lautsprecheranlage')

        if booking.pod == '1':
            einrichtungen.append('Podestelemente')

        if booking.flg == '1':
            einrichtungen.append('Flügel (Saal)')

        if booking.getr == '1':
            einrichtungen.append('Getränke')

        if booking.getr == '1':
            einrichtungen.append('Küche (Saal)')

        if booking.ofk == '1':
            einrichtungen.append('Office (Keller)')

        return {
            'name': booking.anspname or ' '.join((
                member.member_last_name,
                member.member_first_name
            )),
            'telefon': booking.ansptel or member.member_phone,
            'zweck': booking.title,
            'bemerkungen': booking.description,
            'einrichtungen': einrichtungen
        }

    def unescape_dictionary(d):
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = html.unescape(value)
            if isinstance(value, dict):
                d[key] = unescape_dictionary(value)
            if isinstance(value, list):
                d[key] = [html.unescape(v) for v in value]

        return d

    email_fixes = (
        (re.compile(r'2da-capo-rueti.ch$'), '@da-capo.rueti.ch'),
        (re.compile(r'@mzol$'), '@mzol.ch'),
        (re.compile(r'^jo$'), 'info@rueti.ch'),
        (re.compile(r'@pro-vitalis$'), '@pro-vitalis.ch')
    )

    def run_import(request, app):

        # create all resources first, fails if at least one exists already
        print("Creating resources")

        resources = ResourceCollection(app.libres_context)
        floors = {f.id: f.floor_name for f in db.records.floors}
        resources_by_room = {}

        for room in db.records.room:
            resource = resources.add(
                title=title_map.get(room.room_name, room.room_name),
                timezone='Europe/Zurich',
                type='room',
                group=floors[room.floor_id],
                definition=form_definition,
                meta={'is_hidden_from_public': True}
            )

            resources_by_room[room.id] = resource

        # gather all information needed to create the allocations/reservations
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

        # get the user associated with the migration (the first admin)
        users = UserCollection(app.session())
        user = users.query().filter(User.role == 'admin').first()

        if not user:
            abort('No admin user found')

        # get the member mails
        members = {}

        for member in db.records.members:
            members[member.member_id] = member

        # create an allocation for all days between min/max date
        print("Creating allocations")

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

        # create the reservations
        print("Creating reservations")

        booking_conflicts = 0

        for reservation_group, bookings in reservations.items():
            resource = resources_by_room[reservation_group.split('-')[0]]
            scheduler = resource.scheduler
            found_conflict = False

            session_id = uuid4()

            for booking in bookings:
                assert bookings[0].anspmail == booking.anspmail
                assert bookings[0].member_id == booking.member_id
                assert bookings[0].anspname == booking.anspname
                assert bookings[0].ansptel == booking.ansptel
                assert bookings[0].title == booking.title
                assert bookings[0].description == booking.description

                email = booking.anspmail
                email = email or members[booking.member_id].member_email

                for expression, replacement in email_fixes:
                    email = expression.sub(replacement, email)

                try:
                    token = scheduler.reserve(
                        email=email,
                        dates=(
                            isodate.parse_datetime(booking.hour_start),
                            isodate.parse_datetime(booking.hour_end)
                        ),
                        session_id=session_id,
                        single_token_per_session=True,
                        data={'accepted': True}  # accepted through ticket
                    )
                    token = token.hex
                except InvalidEmailAddress:
                    abort("{} is an invalid e-mail address".format(email))
                except AlreadyReservedError:
                    booking_conflicts += 1
                    found_conflict = True

                    print("Booking conflict in {} at {}".format(
                        resource.title, booking.hour_start
                    ))
                    pass

            if found_conflict:
                continue

            forms = FormCollection(app.session())
            form_data = get_formdata(members[booking.member_id], booking)
            form_data = unescape_dictionary(form_data)
            form = resource.form_class(data=form_data)

            if not form.validate():
                abort("{} failed the form check with {}".format(
                    form_data, form.errors
                ))

            submission = forms.submissions.add_external(
                form=form,
                state='pending',
                id=token
            )

            scheduler.queries.confirm_reservations_for_session(session_id)
            scheduler.approve_reservations(token)

            forms.submissions.complete_submission(submission)

            with forms.session.no_autoflush:
                ticket = TicketCollection(request.app.session()).open_ticket(
                    handler_code='RSV', handler_id=token
                )
                ticket.accept_ticket(user)
                ticket.close_ticket()

        if not ignore_booking_conflicts and booking_conflicts:
            abort("There were {} booking conflicts, aborting".format(
                booking_conflicts
            ))

        app.update_ticket_count()

    return run_import
