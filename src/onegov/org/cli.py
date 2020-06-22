""" Provides commands used to initialize org websites. """
from io import BytesIO
from pathlib import Path

import click
import html
import isodate
import re
import requests
import shutil
import textwrap

from cached_property import cached_property
from collections import defaultdict
from datetime import date, datetime, timedelta
from libres.db.models import ReservedSlot
from libres.modules.errors import InvalidEmailAddress, AlreadyReservedError

from onegov.chat import MessageCollection
from onegov.core.crypto import random_token
from onegov.core.custom import json
from onegov.core.cache import lru_cache
from onegov.core.cli import command_group, pass_group_context, abort
from onegov.core.csv import CSVFile
from onegov.core.utils import Bunch
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.event import Event, Occurrence, EventCollection
from onegov.event.collections.events import EventImportItem
from onegov.file import File
from onegov.form import FormCollection
from onegov.org import log
from onegov.org.formats import DigirezDB
from onegov.org.forms.event import TAGS
from onegov.org.models import Organisation, TicketNote, TicketMessage
from onegov.org.forms import ReservationForm
from onegov.pay.models import ManualPayment
from onegov.reservation import Allocation, Reservation
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from onegov.form import as_internal_id, parse_form
from onegov.user import UserCollection, User
from purl import URL
from sedate import replace_timezone, utcnow
from sqlalchemy.dialects.postgresql import array
from sqlalchemy import create_engine, event, text, or_
from sqlalchemy.orm import Session
from tqdm import tqdm
from uuid import UUID, uuid4
from operator import add as add_op

cli = command_group()


@cli.command(context_settings={'creates_path': True})
@click.argument('name')
@click.option('--locale',
              default='de_CH', type=click.Choice(['de_CH', 'fr_CH']))
@pass_group_context
def add(group_context, name, locale):
    """ Adds an org with the given name to the database. For example:

        onegov-org --select '/onegov_org/evilcorp' add "Evilcorp"

    """

    def add_org(request, app):

        if app.session().query(Organisation).first():
            abort("{} already contains an organisation".format(
                group_context.selector))

        app.settings.org.create_new_organisation(app, name, locale=locale)

        click.echo("{} was created successfully".format(name))

    return add_org


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes a single organisation matching the selector.

    Selectors matching multiple organisations are disabled for saftey reasons.

    """

    def delete_org(request, app):

        org = app.org.title
        confirmation = "Do you really want to DELETE {}?".format(org)

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        if app.has_filestorage:
            click.echo("Removing File Storage")

            for item in app.filestorage.listdir('.'):
                if app.filestorage.isdir(item):
                    app.filestorage.removedir(item, recursive=True, force=True)
                else:
                    app.filestorage.remove(item)

        if app.depot_storage_path and app.bound_storage_path:
            click.echo("Removing Depot Storage")
            shutil.rmtree(str(app.bound_storage_path.absolute()))

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
                meta={'access': 'private'}
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
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code='RSV', handler_id=token
                )
                ticket.accept_ticket(user)
                ticket.close_ticket()

        if not ignore_booking_conflicts and booking_conflicts:
            abort("There were {} booking conflicts, aborting".format(
                booking_conflicts
            ))

    return run_import


@cli.command(name='import-reservations', context_settings={'singular': True})
@click.option('--dsn', required=True, help="DSN to the source database")
@click.option('--map', required=True, help="CSV map between resources")
def import_reservations(dsn, map):
    """ Imports reservations from a legacy seantis.reservation system.

    WARNING: Existing reservations and all associated tickets/submissions
    are deleted during the migration.

    Pending reservations are ignored. The expectation is that the old system
    is stopped, then migrated, then never started again.

    Also note that search reindexing is disabled during import. A manual
    reindex is necessary afterwards.

    Example:

    onegov-org --select '/orgs/govikon' import-reservations\
        --dsn postgresql://localhost:5432/legacy\
        --map ressource-map.csv

    The ressource map is a simple CSV file with the following columns:

    * Legacy URL (the URL pointing to the legacy ressource/room)
    * OGC URL (the URL pointing to the associated ressource in the OGC)
    * Type ('daypass' or 'room')

    The first row is expected to be the header row.

    """

    print("Connecting to remote")
    engine = create_engine(dsn).connect()

    @event.listens_for(engine, 'begin')
    def receive_begin(conn):
        conn.execute('SET TRANSACTION READ ONLY')

    remote = Session(bind=engine)

    # define the mapping between old/new resources
    class Mapping(object):

        def __init__(self, libres_context, old_url, new_url, type):
            self.resources = ResourceCollection(libres_context)
            self.old_url = old_url
            self.new_url = new_url
            self.type = type

        @property
        def name(self):
            return URL(self.new_url).path().rstrip('/').split('/')[-1]

        @cached_property
        def resource(self):
            return self.resources.by_name(name=self.name)

        @cached_property
        def old_uuid(self):
            return UUID(requests.get(f'{self.old_url}/@@uuid').text.strip())

        @property
        def new_uuid(self):
            return self.resource.id

    # run the given query returning the query and a count (if possible)
    def select_with_count(session, query, **params):
        query = query.strip(' \n')
        assert query.startswith("SELECT *")

        count = text(
            query
            .replace("SELECT *", "SELECT COUNT(*)", 1)
            .split('ORDER BY')[0]
        )
        count = session.execute(count, params).scalar()

        return count, session.execute(text(query), params)

    # takes a reservation data json and guesses if it was paid
    def was_paid(data):
        data = json.loads(data)

        for definition in data.values():
            for value in definition['values']:
                if is_payment_key(value['key']):
                    return value['value'] == True

        return False

    def is_payment_key(key):
        return key == 'bezahlt'

    print("Reading map")
    records = CSVFile(open(map, 'rb'), ('Old URL', 'New URL', 'Type')).lines
    records = tuple(records)

    # generate forms from the form-data found in the external system
    def get_form_class_and_data(data):

        if not data:
            return ReservationForm, {}

        def exclude(value):
            if as_internal_id(value['desc']) == 'email':
                return True

            if is_payment_key(value['key']):
                return True

        @lru_cache()
        def generate_form_class(formcode):
            return parse_form(formcode, ReservationForm)

        def separate_code_from_data(data):
            fields = []
            values = {}

            for form in sorted(data.values(), key=lambda f: f['desc']):
                fieldset = form['desc']
                fields.append(f"# {fieldset}")

                for v in sorted(form['values'], key=lambda r: r['sortkey']):
                    label = v['desc']
                    id = as_internal_id(f"{fieldset} {label}")

                    # defined on the reservation form
                    if id == 'email':
                        continue

                    if isinstance(v['value'], bool):
                        fields.append(f"{label} = ___")
                        values[id] = v['value'] and "Ja" or "Nein"
                    elif isinstance(v['value'], str):
                        fields.append(f"{label} = ___")
                        values[id] = v['value']
                    elif isinstance(v['value'], datetime):
                        fields.append(f"{label} = YYYY.MM.DD HH:MM")
                        values[id] = v['value']
                    elif isinstance(v['value'], date):
                        fields.append(f"{label} = YYYY.MM.DD")
                        values[id] = v['value']
                    elif isinstance(v['value'], int):
                        fields.append(f"{label} = ___")
                        values[id] = str(v['value'])
                    elif isinstance(v['value'], list):
                        fields.append(f"{label} = ___")
                        values[id] = ', '.join(v['value'])
                    else:
                        raise NotImplementedError((
                            f"No conversion for {v['value']} "
                            f" ({type(v['value'])}"
                        ))

            return '\n'.join(fields), values

        formcode, formdata = separate_code_from_data(data)
        return generate_form_class(formcode), formdata

    def handle_import(request, app):
        session = app.session()

        # disable search indexing during import
        if hasattr(app, 'es_orm_events'):
            app.es_orm_events.stopped = True

        # map the old UUIDs to the resources
        print("Mapping resources")
        mapping = {m.old_uuid: m for m in (
            Mapping(request.app.libres_context, r.old_url, r.new_url, r.type)
            for r in tqdm(records, unit=' resources')
        )}

        print("Clearing existing submissions")
        session.execute(text("""
            DELETE FROM submissions
             WHERE submissions.meta->>'origin' IN :resources
        """), {
            'resources': tuple(m.old_uuid.hex for m in mapping.values())
        })

        print("Clearing existing ticket messages")
        session.execute(text("""
            DELETE from messages
             WHERE channel_id IN (
                SELECT number
                  FROM tickets
                 WHERE tickets.handler_data->>'origin' IN :resources
             )
        """), {
            'resources': tuple(m.old_uuid.hex for m in mapping.values())
        })

        print("Clearing existing tickets")
        session.execute(text("""
            DELETE FROM tickets
             WHERE tickets.handler_data->>'origin' IN :resources
        """), {
            'resources': tuple(m.old_uuid.hex for m in mapping.values())
        })

        payment_ids = tuple(r[0] for r in session.execute(text("""
            SELECT payment_id
            FROM payments_for_reservations_payment
            WHERE reservations_id IN (
                SELECT id
                FROM reservations
                WHERE resource IN :resources
            )
        """), {
            'resources': tuple(m.resource.id for m in mapping.values())
        }))

        if payment_ids:
            print("Clearing existing payments")
            session.execute(text("""
                DELETE FROM payments_for_reservations_payment
                WHERE payment_id IN :payments
            """), {
                'payments': payment_ids
            })

            session.execute(text("""
                DELETE FROM payments
                WHERE id IN :payments
            """), {
                'payments': payment_ids
            })

        print("Clearing existing reservations")
        session.execute(text("""
            DELETE FROM reservations
            WHERE resource IN :resources
        """), {
            'resources': tuple(m.resource.id for m in mapping.values())
        })

        print("Clearing existing reserved slots")
        session.execute(text("""
            DELETE FROM reserved_slots
             WHERE allocation_id IN (
                SELECT id FROM allocations
                 WHERE allocations.mirror_of IN :resources
             )
        """), {
            'resources': tuple(m.resource.id for m in mapping.values())
        })

        print("Clearing existing allocations")
        session.execute(text("""
            DELETE FROM allocations
             WHERE allocations.mirror_of IN :resources
        """), {
            'resources': tuple(m.resource.id for m in mapping.values())
        })

        session.flush()

        print("Fetching remote allocations")
        count, rows = select_with_count(remote, """
            SELECT * FROM allocations
            WHERE mirror_of IN :resources
            ORDER BY allocations.resource
        """, resources=tuple(mapping.keys()))

        # we use a separate id space, so we need to keep track
        allocation_ids = {}

        # the resource might be mapped, but it is not a given
        def row_resource(row):
            if row['resource'] not in mapping:
                return row['resource']

            return mapping[row['resource']].new_uuid

        # create the new allocations
        print("Writing allocations")
        for row in tqdm(rows, unit=' allocations', total=count):
            resource_type = mapping[row['mirror_of']].type

            if row['partly_available'] and resource_type != 'room':
                raise RuntimeError((
                    f"Cannot migrate partly_available allocation "
                    f"to a {resource_type} resource"
                ))

            if row['approve_manually']:
                raise RuntimeError((
                    f"Manually approved allocation found (id: {row['id']}), "
                    f"manually approved allocations are not supported"
                ))

            allocation = Allocation(
                resource=row_resource(row),
                mirror_of=mapping[row['mirror_of']].new_uuid,
                group=row['group'],
                quota=row['quota'],
                quota_limit=row['quota_limit'],
                partly_available=row['partly_available'],
                approve_manually=row['approve_manually'],

                # the timezone was ignored in seantis.reservation
                timezone='Europe/Zurich',
                _start=replace_timezone(row['_start'], 'Europe/Zurich'),
                _end=replace_timezone(row['_end'], 'Europe/Zurich'),

                data=json.loads(row['data']),
                _raster=row['_raster'],
                created=replace_timezone(row['created'], 'UTC'),
                modified=utcnow(),
                type='custom',
            )

            session.add(allocation)
            session.flush()

            allocation_ids[row['id']] = allocation.id

        # fetch the reserved slots that should be migrated
        count, rows = select_with_count(remote, """
            SELECT * FROM reserved_slots WHERE allocation_id IN (
                SELECT id FROM allocations WHERE mirror_of IN :resources
            )
        """, resources=tuple(mapping.keys()))

        # create the reserved slots with the mapped values
        print("Writing reserved slots")
        known = set()
        for row in tqdm(rows, unit=" slots", total=count):
            r = row_resource(row)
            s = replace_timezone(row['start'], 'Europe/Zurich')
            e = replace_timezone(row['end'], 'Europe/Zurich')

            # it's possible for rows to become duplicated after replacing
            # the timezone, if the reserved slot passes over daylight
            # savings time changes
            if (r, s) in known:
                continue

            known.add((r, s))

            session.add(ReservedSlot(
                resource=r,
                start=s,
                end=e,
                allocation_id=allocation_ids[row['allocation_id']],
                reservation_token=row['reservation_token']
            ))

        session.flush()

        # fetch the reservations that should be migrated
        count, rows = select_with_count(remote, """
            SELECT * FROM reservations
            WHERE resource IN :resources
              AND status = 'approved'
            ORDER BY resource
        """, resources=tuple(mapping.keys()))

        def targeted_allocations(group):
            return session.query(Allocation).filter_by(group=group)

        # keep track of custom reservation data, for the creation of tickets
        reservation_data = {}
        payment_states = {}

        print("Writing reservations")
        for row in tqdm(rows, unit=' reservations', total=count):

            reservation_data[row['token']] = {
                'data': json.loads(row['data']),
                'email': row['email'],
                'origin': row['resource'],
                'origin_url': mapping[row['resource']].old_url,
                'created': replace_timezone(row['created'], 'UTC'),
                'modified': replace_timezone(row['modified'], 'UTC'),
            }

            if row['quota'] > 1 and mapping[row.resource].type != 'daypass':
                raise RuntimeError(
                    "Reservations with multiple quotas for rooms "
                    "cannot be migrated"
                )

            # onegov.reservation does not support group targets, so we
            # translate those into normal allocations and create multiple
            # reservations with a shared token
            shared = dict(
                token=row['token'],
                target_type='allocation',
                resource=mapping[row['resource']].new_uuid,
                timezone='Europe/Zurich',
                status=row['status'],
                data={"accepted": True, "migrated": True},
                email=row['email'],
                quota=row['quota'],
                created=replace_timezone(row['created'], 'UTC'),
                modified=replace_timezone(row['modified'], 'UTC'),
                type='custom',
            )

            r = mapping[row['resource']].resource

            if r.pricing_method == 'per_item':
                payment = ManualPayment(
                    amount=r.price_per_item * row['quota'], currency='CHF')
            elif r.pricing_method == 'per_hour':
                raise NotImplementedError()
            else:
                payment = None

            if row['target_type'] == 'group':
                targets = tuple(targeted_allocations(group=row['target']))

                if not targets:
                    raise RuntimeError(f"No rows for target {row['target']}")

                for allocation in targets:
                    allocation.group = uuid4()

                    reservation = Reservation(
                        target=allocation.group,
                        start=allocation.start,
                        end=allocation.end,
                        **shared
                    )

                    if payment:
                        reservation.payment = payment

                    session.add(reservation)

            else:
                reservation = Reservation(
                    target=row['target'],
                    start=replace_timezone(row['start'], 'Europe/Zurich'),
                    end=replace_timezone(row['end'], 'Europe/Zurich'),
                    **shared
                )

                if payment:
                    reservation.payment = payment

                session.add(reservation)

            if reservation.payment:
                if was_paid(row['data']):
                    reservation.payment.state = 'paid'
                    payment_states[row['token']] = 'paid'
                else:
                    payment_states[row['token']] = 'unpaid'

        session.flush()

        # tie reservations to tickets/submissions
        tickets = TicketCollection(session)
        forms = FormCollection(session)

        # the responsible user is the first admin that was added
        user = session.query(User)\
            .filter_by(role='admin')\
            .order_by(User.created).first()

        print("Writing tickets")
        for token, data in tqdm(reservation_data.items(), unit=" tickets"):
            form_class, form_data = get_form_class_and_data(data['data'])

            if form_data:

                # fix common form errors
                if data['email'] == 'info@rischrotkreuz.c':
                    data['email'] = 'info@rischrotkreuz.ch'

                form_data['email'] = data['email']
                form = form_class(data=form_data)

                # wtforms requires raw_data for some validators
                for key, value in form_data.items():
                    getattr(form, key).raw_data = [value]

                submission = forms.submissions.add_external(
                    form=form,
                    state='complete',
                    id=token
                )

                submission.meta['migrated'] = True
                submission.meta['origin'] = data['origin'].hex

            with session.no_autoflush:
                ticket = tickets.open_ticket(
                    handler_code='RSV', handler_id=token.hex)

                ticket.handler_data['migrated'] = True
                ticket.handler_data['origin'] = data['origin'].hex
                ticket.handler_data['origin_url'] = data['origin_url']
                ticket.muted = True
                ticket.state = 'closed'
                ticket.last_state_change = ticket.timestamp()
                ticket.reaction_time = 0
                ticket.user = user
                ticket.created = data['created']
                ticket.modified = data['modified']

                TicketNote.create(ticket, request, (
                    f"Migriert von {data['origin_url']}"
                    f"/reservations?token={token}",
                ), owner=user.username)

    return handle_import


@cli.command(context_settings={'default_selector': '*'})
@click.option('--dry-run', default=False, is_flag=True,
              help="Do not write any changes into the database.")
@pass_group_context
def fix_tags(group_context, dry_run):

    def fixes_german_tags_in_db(request, app):
        session = request.session

        de_transl = app.translations.get('de_CH')

        DEFINED_TAGS = [t[0] for t in TAGS]
        DEFINED_TAG_IDS = [str(s) for s in DEFINED_TAGS]

        def translate(text):
            return text.interpolate(de_transl.gettext(text))

        form_de_to_en = {translate(text): str(text) for text in DEFINED_TAGS}

        predefined = {
            'Theater / Tanz': ('Dancing', 'Theater'),
            'Cultur': ('Culture',),
            'Vortrag / Lesung': ('Talk', 'Reading')
        }

        msg_log = []

        def replace_with_predefined(tags):
            new_tags = tags.copy()
            for t in tags:
                predef = predefined.get(t)
                if predef:
                    new_tags.remove(t)
                    new_tags.extend(predef)
                    if dry_run:
                        msg_log.append(
                            f'{t} -> {", ". join(predef)}')
            return new_tags

        undefined_msg_ids = set()

        def handle_occurrence_tags(occurrence):
            tags = occurrence.tags.copy()
            tags = replace_with_predefined(tags)
            for tag in occurrence.tags:
                if tag in predefined:
                    continue
                if tag not in DEFINED_TAG_IDS:
                    if tag in form_de_to_en:
                        tags.remove(tag)
                        tags.append(form_de_to_en[tag])
                        msg_log.append(
                            f'{tag} -> {form_de_to_en[tag]}')
                    else:
                        undefined_msg_ids.add(tag)
            if tags != occurrence.tags:
                if not dry_run:
                    occurrence.tags = tags

        for event_ in session.query(Event):
            handle_occurrence_tags(event_)

        for occurrence in session.query(Occurrence):
            handle_occurrence_tags(occurrence)

        if dry_run:
            print("\n".join(set(msg_log)))

        assert not undefined_msg_ids, f'Define ' \
                                      f'{", ".join(undefined_msg_ids)}' \
                                      f' in org/forms/event.py'

    return fixes_german_tags_in_db


def close_ticket(ticket, user, request):
    if ticket.state == 'open':
        ticket.accept_ticket(user)
        TicketMessage.create(
            ticket,
            request,
            'opened'
        )

    TicketMessage.create(
        ticket,
        request,
        'closed'
    )
    ticket.close_ticket()


@cli.command('fetch')
@pass_group_context
@click.option('--source', multiple=True)
@click.option('--tag', multiple=True)
@click.option('--location', multiple=True)
@click.option('--create-tickets', is_flag=True, default=False)
@click.option('--state-transfers', multiple=True,
              help="Usage: local:remote, e.g. published:withdrawn")
@click.option('--published-only', is_flag=True, default=False,
              help='Only add event is they are publised on remote')
@click.option('--delete-orphaned-tickets', is_flag=True)
def fetch(group_context, source, tag, location, create_tickets,
          state_transfers, published_only, delete_orphaned_tickets):
    """ Fetches events from other instances.

    Only fetches events from the same namespace which have not been imported
    themselves.

    Example

        onegov-org --select '/veranstaltungen/zug' fetch \
            --source menzingen --source steinhausen
            --tag Sport --tag Konzert
            --location Zug

    Additional parameters:

            --state-transfers published:withdrawn

            Will update the local event.state from published to withdrawn
            automatically. If there are any tickets associated with the event,
            the will be closed automatically.

            --pusblished_only:
            When passing the remote items to the EventCollection, only add
            events if they are published.

            --delete-orphaned-tickets

            Delete Tickets, TicketNotes and TicketMessasges if an
            event gets deleted automatically.

    The following example will close tickets automatically for
    submitted and published events that were withdrawn on the remote.

    onegov-event --select '/veranstaltungen/zug' fetch \
            --source menzingen --source steinhausen
            --published-only
            --create-tickets
            --state-transfers published:withdrawn
            --state-transfers submitted:withdrawm

    """

    def vector_add(a, b):
        return list(map(add_op, a, b))

    if not len(source):
        abort("Provide at least one source")

    valid_state_transfers = {}
    valid_choices = ('initiated', 'submitted', 'published', 'withdrawn')
    if len(state_transfers):
        for string in state_transfers:
            local, remote = string.split(':')
            assert local, remote
            assert local in valid_choices
            assert remote in valid_choices
            valid_state_transfers[local] = remote

    def _fetch(request, app):

        def event_file(reference):
            # XXX use a proper depot manager for this
            path = Path(app.depot_storage_path) / reference['path'] / 'file'
            with open(path):
                content = BytesIO(path.open('rb').read())
            return content

        try:
            result = [0, 0, 0]

            for key in source:
                remote_schema = '{}-{}'.format(app.namespace, key)
                local_schema = app.session_manager.current_schema
                assert remote_schema in app.session_manager.list_schemas()

                app.session_manager.set_current_schema(remote_schema)
                remote_session = app.session_manager.session()
                assert remote_session.info['schema'] == remote_schema

                query = remote_session.query(Event)
                query = query.filter(
                    or_(
                        Event.meta['source'].astext.is_(None),
                        Event.meta['source'].astext == ''
                    )
                )
                if tag:
                    query = query.filter(Event._tags.has_any(array(tag)))
                if location:
                    query = query.filter(
                        or_(*[
                            Event.location.op('~')(f'\\y{term}\\y')
                            for term in location
                        ])
                    )

                def remote_events():
                    for event_ in query:
                        event_._es_skip = True
                        yield EventImportItem(
                            event=Event(
                                state=event_.state,
                                title=event_.title,
                                start=event_.start,
                                end=event_.end,
                                timezone=event_.timezone,
                                recurrence=event_.recurrence,
                                content=event_.content,
                                location=event_.location,
                                tags=event_.tags,
                                source=f'fetch-{key}-{event_.name}',
                                coordinates=event_.coordinates,
                                organizer=event_.organizer,
                                organizer_email=event_.organizer_email,
                                price=event_.price,
                            ),
                            image=(
                                event_file(event_.image.reference)
                                if event_.image else None
                            ),
                            image_filename=(
                                event_.image.name
                                if event_.image else None
                            ),
                            pdf=(
                                event_file(event_.pdf.reference)
                                if event_.pdf else None
                            ),
                            pdf_filename=(
                                event_.pdf.name
                                if event_.pdf else None
                            )
                        )

                # be sure to switch back to the local schema, lest we
                # accidentally update things on the remote
                app.session_manager.set_current_schema(local_schema)
                local_session = app.session_manager.session()
                local_events = EventCollection(local_session)

                # the responsible user is the first admin that was added
                local_admin = local_session.query(User) \
                    .filter_by(role='admin') \
                    .order_by(User.created).first()

                if create_tickets and not local_admin:
                    abort("Can not create tickets, no admin is registered")

                def ticket_for_event(event_id):
                    return TicketCollection(local_session).by_handler_id(
                        event_id.hex)

                helper_request = Bunch(
                    current_username=local_admin.username,
                    session=local_session)

                added, updated, purged = local_events.from_import(
                    remote_events(),
                    purge=f'fetch-{key}',
                    publish_immediately=False,
                    valid_state_transfers=valid_state_transfers,
                    published_only=published_only
                )

                for event_ in added:
                    event_.submit()
                    if not create_tickets:
                        event_.publish()
                        continue

                    with local_session.no_autoflush:
                        tickets = TicketCollection(local_session)
                        new_ticket = tickets.open_ticket(
                            handler_code='EVN', handler_id=event_.id.hex,
                            source=event_.meta['source'],
                            user=local_admin.username
                        )
                        new_ticket.muted = True
                        TicketNote.create(new_ticket, request, (
                            f"Importiert von Instanz {key}"

                        ), owner=local_admin.username)

                for event_id in purged:
                    ticket = ticket_for_event(event_id)
                    if ticket:
                        if not delete_orphaned_tickets:
                            close_ticket(ticket, local_admin, helper_request)
                        else:
                            messages = MessageCollection(
                                local_session,
                                channel_id=ticket.number
                            )
                            for msg in messages.query():
                                local_session.delete(msg)
                            local_session.delete(ticket)

                result = vector_add(
                    result,
                    (len(added), len(updated), len(purged))
                )

            click.secho(
                f"Events successfully fetched "
                f"({result[0]} added, {result[1]} updated, "
                f"{result[2]} deleted)",
                fg='green'
            )

        except Exception as e:
            log.error("Error fetching events", exc_info=True)
            raise(e)

    return _fetch


@cli.command('fix-directory-files')
@pass_group_context
def fix_directory_files(group_context):
    """
    Not sure of this doubles the files, but actually the file
    reference remains, so it shouldn't

    This command will become obsolete as soon as the type of files in
    submissions are set correctly with type 'directory'.

    """
    def execute(request, app):
        count = 0
        for entry in request.session.query(DirectoryEntry).all():
            for field in entry.directory.file_fields:
                field_data = entry.content['values'][field.id]
                if field_data and field_data.get('data', '').startswith('@'):
                    file_id = field_data['data'].lstrip('@')
                    file = request.session.query(File).filter_by(
                        id=file_id).first()
                    if file and not file.type == 'directory':
                        new = DirectoryFile(
                            id=random_token(),
                            name=file.name,
                            note=file.note,
                            reference=file.reference
                        )
                        entry.files.append(new)
                        entry.content['values'][field.id]['data'] = \
                            f'@{new.id}'
                        entry.content.changed()
                        count += 1
        if count:
            click.secho(
                f"{app.schema} - {count} files adapted with type `directory`",
                fg='green'
            )
    return execute
