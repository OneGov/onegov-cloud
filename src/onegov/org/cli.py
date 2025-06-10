""" Provides commands used to initialize org websites. """
from __future__ import annotations

import json
import click
import html
import isodate
import re
import shutil
import sys
import textwrap

from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import date, datetime, timedelta
from io import BytesIO

from openpyxl import load_workbook
import yaml
from onegov.core.orm.utils import QueryChain
from libres.modules.errors import (InvalidEmailAddress, AlreadyReservedError,
                                   TimerangeTooLong)
from onegov.chat import MessageCollection
from onegov.core.cli import command_group, pass_group_context, abort
from onegov.core.crypto import random_token
from onegov.core.utils import Bunch
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.event import Event, Occurrence, EventCollection
from onegov.event.collections.events import EventImportItem
from onegov.file import File
from onegov.form import FormCollection, FormDefinition
from onegov.org import log
from onegov.org.formats import DigirezDB
from onegov.org.forms.event import TAGS
from onegov.org.management import LinkMigration
from onegov.org.models.page import Page
from onegov.org.models import ExtendedDirectory
from onegov.org.models import Organisation, TicketNote, TicketMessage
from onegov.org.models.resource import Resource
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from onegov.town6.upgrade import migrate_homepage_structure_for_town6
from onegov.town6.upgrade import migrate_theme_options
from onegov.user.models import TAN
from onegov.user import UserCollection, User
from operator import add as add_op
from pathlib import Path
from sqlalchemy import func, and_, or_
from sqlalchemy.dialects.postgresql import array
from uuid import uuid4


from typing import IO, Any, TYPE_CHECKING, TypedDict
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from depot.fields.upload import UploadedFile
    from onegov.core.cli.core import GroupContext
    from onegov.core.csv import DefaultRow
    from onegov.core.upgrade import UpgradeContext
    from onegov.org.app import OrgApp
    from onegov.org.request import OrgRequest
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Query, Session
    from translationstring import TranslationString
    from uuid import UUID


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@click.argument('name')
@click.option(
    '--locale',
    default='de_CH',
    type=click.Choice(['de_CH', 'fr_CH', 'it_CH'])
)
@pass_group_context
def add(
    group_context: GroupContext,
    name: str,
    locale: str
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Adds an org with the given name to the database. For example:

    .. code-block:: bash

        onegov-org --select '/onegov_org/evilcorp' add "Evilcorp"

    """

    def add_org(request: OrgRequest, app: OrgApp) -> None:

        if app.session().query(Organisation).first():
            abort('{} already contains an organisation'.format(
                group_context.selector))

        app.settings.org.create_new_organisation(app, name, locale=locale)

        click.echo('{} was created successfully'.format(name))

    return add_org


@cli.command(name='import-digirez', context_settings={'singular': True})
@click.argument('accessdb', type=click.Path(exists=True, resolve_path=True))
@click.option('--min-date', default=None,
              help="Min date in the form '2016-12-31'")
@click.option('--ignore-booking-conflicts', default=False, is_flag=True,
              help='Ignore booking conflicts (TESTING ONlY)')
def import_digirez(
    accessdb: str,
    min_date: str,
    ignore_booking_conflicts: bool
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Imports a Digirez reservation database into onegov.org.

    Example:
    .. code-block:: bash

        onegov-org --select '/orgs/govikon' import-digirez room_booking.mdb

    """

    if not shutil.which('mdb-export'):
        abort("Could not find 'mdb-export', please install mdbtools!")

    min_date_ = min_date and isodate.parse_date(min_date) or date.today()
    min_dt = datetime(min_date_.year, min_date_.month, min_date_.day)

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

    def get_formdata(
        member: DefaultRow,
        booking: DefaultRow
    ) -> dict[str, Any]:

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
            'name': booking.anspname or (
                f'{member.member_last_name} {member.member_first_name}'),
            'telefon': booking.ansptel or member.member_phone,
            'zweck': booking.title,
            'bemerkungen': booking.description,
            'einrichtungen': einrichtungen
        }

    def unescape_dictionary(d: dict[str, Any]) -> dict[str, Any]:
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

    def run_import(request: OrgRequest, app: OrgApp) -> None:

        # create all resources first, fails if at least one exists already
        click.echo('Creating resources')

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
            if isodate.parse_datetime(b.hour_end) > min_dt
        )

        # group by room id in addition to the multi_id, as digirez supports
        # reservations which span multiple rooms
        reservations = defaultdict(list)

        for booking in relevant_bookings:
            group = f'{booking.room_id}-{booking.multi_id}'
            reservations[group].append(booking)

        # get the max_date per resource
        max_dates = {}

        for reservation_group in reservations:
            resource_id = resources_by_room[reservation_group.split('-')[0]].id

            if resource_id not in max_dates:
                max_dates[resource_id] = min_dt

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
        click.echo('Creating allocations')

        for resource in resources_by_room.values():

            # true if the resource does not have any bookings
            if resource.id not in max_dates:
                continue

            assert resource.group is not None
            start_hour, end_hour = floor_hours[resource.group]
            days = (max_dates[resource.id].date() - min_dt.date()).days

            first_day_start = datetime(
                min_dt.year, min_dt.month, min_dt.day,
                start_hour
            )

            first_day_end = datetime(
                min_dt.year, min_dt.month, min_dt.day,
                end_hour - 1, 59, 59, 999999
            )

            whole_day = (start_hour, end_hour) == (0, 24)

            for day in range(days + 1):
                start = first_day_start + timedelta(days=day)
                end = first_day_end + timedelta(days=day)

                resource.scheduler.allocate(
                    dates=(start, end),
                    partly_available=True,
                    whole_day=whole_day,
                )

        # create the reservations
        click.echo('Creating reservations')

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
                    token_uuid = scheduler.reserve(
                        email=email,
                        dates=(
                            isodate.parse_datetime(booking.hour_start),
                            isodate.parse_datetime(booking.hour_end)
                        ),
                        session_id=session_id,
                        single_token_per_session=True,
                        data={'accepted': True}  # accepted through ticket
                    )
                    token = token_uuid.hex
                except InvalidEmailAddress:
                    abort(f'{email} is an invalid e-mail address')
                except AlreadyReservedError:
                    booking_conflicts += 1
                    found_conflict = True

                    click.echo(
                        f'Booking conflict in {resource.title} '
                        f'at {booking.hour_start}'
                    )

            if found_conflict:
                continue

            assert resource.form_class is not None
            forms = FormCollection(app.session())
            form_data = get_formdata(members[booking.member_id], booking)
            form_data = unescape_dictionary(form_data)
            form = resource.form_class(data=form_data)

            if not form.validate():
                abort(f'{form_data} failed the form check with {form.errors}')

            submission = forms.submissions.add_external(
                form=form,
                state='pending',
                id=token_uuid
            )

            scheduler.queries.confirm_reservations_for_session(session_id)
            scheduler.approve_reservations(token_uuid)

            forms.submissions.complete_submission(submission)

            with forms.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code='RSV', handler_id=token
                )
                ticket.accept_ticket(user)
                ticket.close_ticket()

        if not ignore_booking_conflicts and booking_conflicts:
            abort(
                f'There were {booking_conflicts} booking conflicts, aborting'
            )

    return run_import


@cli.command(context_settings={'default_selector': '*'})
@click.option('--dry-run', default=False, is_flag=True,
              help='Do not write any changes into the database.')
@pass_group_context
def fix_tags(
    group_context: GroupContext,
    dry_run: bool
) -> Callable[[OrgRequest, OrgApp], None]:

    def fixes_german_tags_in_db(request: OrgRequest, app: OrgApp) -> None:
        session = request.session

        de_transl = app.translations.get('de_CH')
        assert de_transl is not None

        defined_tags = list(TAGS)
        defined_tag_ids = [str(s) for s in defined_tags]

        def translate(text: TranslationString) -> str:
            return text.interpolate(de_transl.gettext(text))

        form_de_to_en = {translate(text): str(text) for text in defined_tags}

        predefined = {
            'Theater / Tanz': ('Dancing', 'Theater'),
            'Cultur': ('Culture',),
            'Vortrag / Lesung': ('Talk', 'Reading')
        }

        msg_log = []

        def replace_with_predefined(
            tags: list[str]
        ) -> list[str]:

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

        def handle_occurrence_tags(occurrence: Event | Occurrence) -> None:
            tags = occurrence.tags.copy()
            tags = replace_with_predefined(tags)
            for tag in occurrence.tags:
                if tag in predefined:
                    continue
                if tag not in defined_tag_ids:
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
            click.echo('\n'.join(set(msg_log)))

        assert not undefined_msg_ids, (
            f'Define {", ".join(undefined_msg_ids)}'
            f' in org/forms/event.py'
        )

    return fixes_german_tags_in_db


def close_ticket(ticket: Ticket, user: User, request: OrgRequest) -> None:
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
              help='Usage: local:remote, e.g. published:withdrawn')
@click.option('--published-only', is_flag=True, default=False,
              help='Only add event is they are published on remote')
@click.option('--delete-orphaned-tickets', is_flag=True)
def fetch(
    group_context: GroupContext,
    source: Sequence[str],
    tag: Sequence[str],
    location: Sequence[str],
    create_tickets: bool,
    state_transfers: Sequence[str],
    published_only: bool,
    delete_orphaned_tickets: bool
) -> Callable[[OrgRequest, OrgApp], None]:
    r""" Fetches events from other instances.

    Only fetches events from the same namespace which have not been imported
    themselves.

    Example
    .. code-block:: bash

        onegov-org --select '/veranstaltungen/zug' fetch \
            --source menzingen --source steinhausen \
            --tag Sport --tag Konzert \
            --location Zug

    Additional parameters:

    - ``--state-transfers published:withdrawn``

        Will update the local event.state from published to withdrawn
        automatically. If there are any tickets associated with the event,
        the will be closed automatically.

    - ``--pusblished-only``

        When passing the remote items to the EventCollection, only add
        events if they are published.

    - ``--delete-orphaned-tickets``

        Delete Tickets, TicketNotes and TicketMessasges if an
        event gets deleted automatically.

    The following example will close tickets automatically for
    submitted and published events that were withdrawn on the remote.

    .. code-block:: bash
        onegov-event --select '/veranstaltungen/zug' fetch \
            --source menzingen --source steinhausen \
            --published-only \
            --create-tickets \
            --state-transfers published:withdrawn \
            --state-transfers submitted:withdrawm

    """

    def vector_add(a: Sequence[int], b: Sequence[int]) -> list[int]:
        return list(map(add_op, a, b))

    if not len(source):
        abort('Provide at least one source')

    valid_state_transfers = {}
    valid_choices = ('initiated', 'submitted', 'published', 'withdrawn')
    if len(state_transfers):
        for string in state_transfers:
            local, remote = string.split(':')
            assert local, remote
            assert local in valid_choices
            assert remote in valid_choices
            valid_state_transfers[local] = remote

    def _fetch(request: OrgRequest, app: OrgApp) -> None:

        def event_file(reference: UploadedFile) -> BytesIO:
            # XXX use a proper depot manager for this
            assert app.depot_storage_path is not None
            path = Path(app.depot_storage_path) / reference['path'] / 'file'
            with open(path):
                content = BytesIO(path.open('rb').read())
            return content

        try:
            result = [0, 0, 0]

            for key in source:
                remote_schema = f'{app.namespace}-{key}'
                local_schema = app.session_manager.current_schema
                assert local_schema is not None
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
                    query = query.filter(
                        Event._tags.has_any(array(tag))  # type:ignore
                    )
                if location:
                    query = query.filter(
                        or_(*(
                            Event.location.op('~')(f'\\y{term}\\y')
                            for term in location
                        ))
                    )

                def remote_events(
                    query: Query[Event] = query,
                    key: str = key
                ) -> Iterator[EventImportItem]:

                    for event_ in query:
                        event_._es_skip = True
                        yield EventImportItem(
                            event=Event(  # type:ignore[misc]
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
                                organizer_phone=event_.organizer_phone,
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
                local_admin = (
                    local_session.query(User)
                    .filter_by(role='admin')
                    .order_by(User.created).first()
                )

                if create_tickets and not local_admin:
                    abort('Can not create tickets, no admin is registered')

                def ticket_for_event(
                    event_id: UUID,
                    local_session: Session = local_session
                ) -> Ticket | None:
                    return TicketCollection(local_session).by_handler_id(
                        event_id.hex)

                added, updated, purged = local_events.from_import(
                    remote_events(),
                    to_purge=[f'fetch-{key}'],
                    publish_immediately=False,
                    valid_state_transfers=valid_state_transfers,
                    published_only=published_only
                )

                for event_ in added:
                    event_.submit()
                    if not create_tickets:
                        event_.publish()
                        continue

                    assert local_admin is not None
                    with local_session.no_autoflush:
                        tickets = TicketCollection(local_session)
                        new_ticket = tickets.open_ticket(
                            handler_code='EVN', handler_id=event_.id.hex,
                            source=event_.meta['source'],
                            user=local_admin.username
                        )
                        new_ticket.muted = True
                        TicketNote.create(new_ticket, request, (
                            f'Importiert von Instanz {key}'

                        ), owner=local_admin.username)

                helper_request: OrgRequest = Bunch(  # type:ignore
                    current_username=local_admin and local_admin.username,
                    session=local_session)

                for event_id in purged:
                    ticket = ticket_for_event(event_id)
                    if ticket:
                        if not delete_orphaned_tickets:
                            if local_admin is None:
                                abort(
                                    'Can not close orphaned ticket, '
                                    'no admin is registered'
                                )
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
                f'Events successfully fetched '
                f'({result[0]} added, {result[1]} updated, '
                f'{result[2]} deleted)',
                fg='green'
            )

        except Exception:
            log.exception('Error fetching events')
            raise

    return _fetch


@cli.command('fix-directory-files')
@pass_group_context
def fix_directory_files(
    group_context: GroupContext
) -> Callable[[OrgRequest, OrgApp], None]:
    """
    Not sure of this doubles the files, but actually the file
    reference remains, so it shouldn't

    This command will become obsolete as soon as the type of files in
    submissions are set correctly with type 'directory'.

    """
    def execute(request: OrgRequest, app: OrgApp) -> None:
        count = 0
        for entry in request.session.query(DirectoryEntry).all():
            for field in entry.directory.file_fields:
                field_data = entry.content['values'][field.id]
                if field_data and field_data.get('data', '').startswith('@'):
                    file_id = field_data['data'].lstrip('@')
                    file = request.session.query(File).filter_by(
                        id=file_id).first()
                    if file and file.type != 'directory':
                        new = DirectoryFile(  # type:ignore[misc]
                            id=random_token(),
                            name=file.name,
                            note=file.note,
                            reference=file.reference
                        )
                        entry.files.append(new)
                        entry.content['values'][field.id][
                            'data'] = f'@{new.id}'
                        entry.content.changed()  # type:ignore[attr-defined]
                        count += 1
        if count:
            click.secho(
                f'{app.schema} - {count} files adapted with type `directory`',
                fg='green'
            )
    return execute


@cli.command('migrate-town', context_settings={'singular': True})
@pass_group_context
def migrate_town(
    group_context: GroupContext
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Migrates the database from an old town to the new town like in the
    upgrades.

    """

    def migrate_to_new_town(request: OrgRequest, app: OrgApp) -> None:
        context: UpgradeContext = Bunch(session=app.session())  # type:ignore
        migrate_theme_options(context)
        migrate_homepage_structure_for_town6(context)

    return migrate_to_new_town


@cli.command('migrate-links', context_settings={'singular': True})
@pass_group_context
@click.argument('old-uri')
@click.option('--dry-run', is_flag=True, default=False)
def migrate_links_cli(
    group_context: GroupContext,
    old_uri: str,
    dry_run: bool
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Migrates url's in pages. Supports domains and full urls. Most of
    the urls are located in meta and content fields.
    """

    if '.' not in old_uri:
        click.secho('Domain must contain a dot')
        sys.exit(1)

    def execute(request: OrgRequest, app: OrgApp) -> None:
        if old_uri.startswith('http'):
            new_uri = request.host_url
        else:
            new_uri = request.domain
        migration = LinkMigration(request, old_uri=old_uri, new_uri=new_uri)
        total, grouped_count = migration.migrate_site_collection(
            test=dry_run
        )

        if total:
            click.secho(f'Total replaced: {total}')
            click.secho('Replaced links by group:')
            for group, counts in grouped_count.items():
                for field, count in counts.items():
                    if count:
                        click.secho(f'{group}.{field}: {count}')
        else:
            click.secho('Nothing found')

    return execute


@cli.command(context_settings={'default_selector': '*'})
@pass_group_context
def migrate_publications(
    group_context: GroupContext,
    dry_run: bool
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Marks signed files for publication. """

    def mark_as_published(request: OrgRequest, app: OrgApp) -> None:
        session = request.session
        files = session.query(File).filter_by(signed=True).all()
        for file in files:
            file.publication = True
        if files:
            click.echo(
                f'{session.info["schema"]}: '
                f'Marked {len(files)} signed files for publication'
            )

    return mark_as_published


@cli.command(name='delete-invisible-links')
def delete_invisible_links() -> Callable[[OrgRequest, OrgApp], None]:
    """ Deletes all the data associated with a period, including:

    Example:
    .. code-block:: bash

        onegov-org --select /foo/bar delete-invisible-links

    """

    def delete_invisible_links(request: OrgRequest, app: OrgApp) -> None:
        session = request.session
        query = QueryChain(
            (session.query(Page),
             session.query(Resource),
             session.query(ExtendedDirectory),
             session.query(FormDefinition))
        )  # type:ignore
        models = query.all()

        click.echo(click.style(
            {session.info['schema']},
            fg='yellow'
        ))

        invisible_links = []
        for page in models:
            # Find links with no text, only br tags and/or whitespaces
            for field in page.content_fields_containing_links_to_files:
                if not page.content.get(field):
                    continue
                soup = BeautifulSoup(page.content.get(field), 'html.parser')
                for link in soup.find_all('a'):
                    if not any(
                        tag.name != 'br' and (
                            tag.name or not tag.isspace()
                        ) for tag in link.contents
                    ):
                        invisible_links.append(link)
                        if all(tag.name == 'br' for tag in link.contents):
                            link.replace_with(
                                BeautifulSoup('<br/>', 'html.parser')
                            )
                        else:
                            link.decompose()

                # Save the modified HTML back to page.text
                if page.content[field] != str(soup):
                    page.content[field] = str(soup)

        click.echo(
            click.style(
                f'{session.info["schema"]}: '
                f'Deleted {len(invisible_links)} invisible links',
                fg='yellow'
            )
        )

    return delete_invisible_links


@cli.command(name='get-resources-and-forms')
@click.argument('option_file', type=click.File('rb'))
def get_resources_and_forms(
    option_file: IO[bytes]
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Get the resources and forms from the option file. """

    def print_resources_and_forms(request: OrgRequest, app: OrgApp) -> None:
        book = load_workbook(option_file)
        sheet = book['Reservationen']

        class OptionDict(TypedDict):
            options: set[str]
            type: str

        resources: dict[str, dict[str, OptionDict]] = {}
        for index, row in enumerate(sheet.rows):
            if index <= 3:
                continue
            for i, cell in enumerate(row):
                value = str(cell.value)
                if i == 0:
                    resource_name = value
                    if resource_name not in resources:
                        resources[resource_name] = {}
                if i == 13:  # Option name
                    option = value
                    if resources[resource_name].get(option) is None:
                        resources[resource_name][option] = {
                            'type': 'text',
                            'options': set()
                        }
                if i == 14:  # Option answer
                    answer = value
                    resources[resource_name][option]['options'].add(answer)
                if i == 15:  # Option price
                    if int(value) > 0:
                        resources[resource_name][option]['options'].remove(
                            answer)
                        answer = answer.replace(' (', ', ').replace(
                            ')', '') + f' ({value} CHF)'
                        resources[resource_name][option]['options'].add(
                            answer)
                        resources[resource_name][option]['type'] = 'radio'

        for resource in resources.keys():
            click.secho(resource, fg='blue')
            for option in resources[resource]:
                if resources[resource][option]['type'] == 'text':
                    click.secho(f'{option} = ___', fg='cyan')
                else:
                    click.secho(f'{option} =', fg='cyan')
                    for answer in resources[resource][option]['options']:
                        click.echo(f'    ( ) {answer}',)

    return print_resources_and_forms


@cli.command(name='import-reservations', context_settings={'singular': True})
@click.argument('reservation_file', type=click.File('rb'))
@click.argument('option_file', type=click.File('rb'))
@click.argument('mapping_yaml', type=click.File('rb'))
@click.option('--dry-run', is_flag=True, default=False)
def import_reservations(
    reservation_file: IO[bytes],
    option_file: IO[bytes],
    mapping_yaml: IO[bytes],
    dry_run: bool
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Imports reservations from a Excel file (needs to be .xlsx).
    Creates no resources or allocations, so the availabilty periods need to
    be set in the resource settings.
    """

    def import_reservations(request: OrgRequest, app: OrgApp) -> None:

        class Reservation(TypedDict):
            general: dict[str, Any]
            fields: dict[str, Any]
            dates: list[Any]

        yaml_file = mapping_yaml.read()
        yaml_dict = yaml.safe_load(yaml_file)
        shared_fields = yaml_dict.get('shared_fields', {})
        resource_options = yaml_dict.get('resource_options', {})

        book = load_workbook(reservation_file)
        sheet = book['Reservationsdaten']

        book_options = load_workbook(option_file)
        sheet_options = book_options['Reservationen']

        reservations: dict[
            str, dict[str, Reservation]] = {}
        count = 0
        last_reservation_id = ''
        for index, row in enumerate(sheet.rows):
            if index <= 3:  # Skip the first 3 rows, they are headers
                continue

            reservation: Reservation = {
                'general': {},
                'fields': {},
                'dates': []
            }
            row_empty: bool = True
            id = ''
            resource_name = ''

            for i, cell in enumerate(row):
                value = cell.value
                if i == 0:
                    if value is None:
                        continue
                    row_empty = False
                    resource_name = str(value)
                elif i == 3:
                    id = str(value)
                    if last_reservation_id == id:
                        reservation = reservations[resource_name][id]
                elif i == 6 or i == 8:
                    reservation['dates'].append(value)
                elif i == 22:
                    if value is None:
                        value = 'info@seantis.ch'
                    reservation['general']['email'] = value
                elif i in shared_fields:
                    value = str(value or '-')
                    key = shared_fields[i]
                    if reservation['fields'].get(key) is None:
                        reservation['fields'][key] = value
                    elif value not in reservation['fields'][key]:
                        if i == 17 or i == 18:
                            reservation['fields'][key] += f' {value}'
                        else:
                            reservation['fields'][key] += f', {value}'

            if not row_empty:
                # Check if the dates spread across multiple days
                start = reservation['dates'][-2]
                end = reservation['dates'][-1]
                if start.day != end.day:
                    days = (end - start).days + 1
                    for day in range(days):
                        reservation['dates'].insert(
                            -1, start + timedelta(days=day)
                        ) if day != 0 else None
                        end_of_day = datetime.combine(
                            start, end.time()
                        )
                        reservation['dates'].insert(
                            -1, end_of_day + timedelta(days=day)
                        ) if day != days - 1 else None
                count += 1
                if resource_name not in reservations:
                    reservations[resource_name] = {}

                if id not in reservations[resource_name] and (
                    id != last_reservation_id
                ):
                    reservations[resource_name][id] = reservation
                last_reservation_id = id or ''

        options_count = 0
        options_not_found = set()
        for index, row in enumerate(sheet_options.rows):
            row_empty = True
            if index <= 3:
                continue
            for i, cell in enumerate(row):
                value = cell.value
                if value is None:
                    continue
                row_empty = False
                options_count += 1
                if i == 0:
                    resource_name = str(value)
                elif i == 2:
                    id = str(value)
                elif resource_name in reservations:
                    if id in reservations[resource_name]:
                        if i == 13:  # Option name
                            key = resource_options[resource_name][
                                'options'].get(value)
                            if key is None:
                                options_not_found.add(
                                    f'{resource_name}: {value}')
                        if i == 14:  # Option answer
                            if key is not None:
                                reservation = reservations[resource_name][id]
                                if reservation['fields'].get(key) is None:
                                    reservation['fields'][key] = value
        for option in options_not_found:
            click.secho(f'Option not found in the mapping file: {option}',
                        fg='yellow')

        if dry_run:
            res_show = json.dumps(reservations, indent=4, default=str)
            click.secho(f'Reservations: {res_show}', fg='green')

        # Create reservations
        if not dry_run:
            resources = ResourceCollection(app.libres_context)
            for resource_name in reservations.keys():

                real_resource_name = resource_options[resource_name]['name']
                resource = resources.by_name(real_resource_name.lower())

                if not resource:
                    click.echo(
                        f'Resource {resource} not found in the database'
                    )
                    continue

                click.echo(
                    f'Importing reservations for {resource.title}'
                )
                scheduler = resource.scheduler

                for id, reservation in reservations[resource_name].items():
                    found_conflict = False
                    session_id = uuid4()
                    for n in range(int(len(reservation['dates'])/2)):
                        email = reservation['general'].get('email')
                        start = reservation['dates'][n*2]
                        end = reservation['dates'][n*2+1]

                        try:
                            token_uuid = scheduler.reserve(
                                email=str(email),
                                dates=(start, end),
                                session_id=session_id,
                                single_token_per_session=True,
                                data={'accepted': True}
                            )
                            token = token_uuid.hex
                        except InvalidEmailAddress:
                            abort(f'{email} is an invalid e-mail address')
                        except AlreadyReservedError:
                            found_conflict = True
                            click.secho(
                                f'Booking conflict in {resource.title} '
                                f'at {start}', fg='red')
                        except TimerangeTooLong:
                            found_conflict = True
                            click.secho(
                                f'Timerange too long in {resource.title} '
                                f'at {start} - {end}', fg='red')
                            rules = resource.content['rules']
                            relevant_rules = []
                            for rule in rules:
                                rule = rule['options']
                                if rule['start'] <= start.date(
                                ) and rule['end'] >= end.date(
                                ) and start.weekday(
                                ) not in rule['except_for'] and start.time(
                                ) <= rule['start_time'] and end.time(
                                ) >= rule['end_time']:
                                    relevant_rules.append(rule)
                            for i, rule in enumerate(relevant_rules):
                                start = datetime.combine(
                                    start.date(), rule['start_time'])
                                end = datetime.combine(
                                    end.date(), rule['end_time'])
                                token_uuid = scheduler.reserve(
                                    email=str(email),
                                    dates=(start, end),
                                    session_id=session_id,
                                    single_token_per_session=True,
                                    data={'accepted': True}
                                )
                                token = token_uuid.hex
                            if not relevant_rules:
                                click.secho(
                                    f'No rules found for {resource.title} '
                                    f'at {start}', fg='red')

                    if found_conflict:
                        continue

                    assert resource.form_class is not None
                    forms = FormCollection(app.session())

                    form_data = {}
                    for key, value in reservation['fields'].items():
                        form_data[key] = str(value)

                    form = resource.form_class(data=form_data)

                    if not form.validate():
                        abort(f'{form_data} failed the form check'
                            f' with {form.errors}')

                    submission = forms.submissions.add_external(
                        form=form,
                        state='pending',
                        id=token_uuid
                    )

                    scheduler.queries.confirm_reservations_for_session(
                        session_id)
                    scheduler.approve_reservations(token_uuid)

                    forms.submissions.complete_submission(submission)

                    users = UserCollection(app.session())
                    user = users.query().filter(
                        User.username == 'info@seantis.ch').first()

                    if not user:
                        abort('info@seantis.ch not found in users')

                    with forms.session.no_autoflush:
                        ticket = TicketCollection(request.session).open_ticket(
                            handler_code='RSV', handler_id=token
                        )
                        ticket.accept_ticket(user)
                        ticket.close_ticket()

                    click.secho(f'Sucessfully imported reservation {id}',
                                fg='green')

    return import_reservations


@cli.command(context_settings={'default_selector': '*'})
@click.argument('year', type=click.IntRange(1900, date.today().year))
@click.argument('month', type=click.IntRange(1, 12))
@pass_group_context
def mtan_statistics(
    group_context: GroupContext,
    year: int,
    month: int,
) -> Callable[[OrgRequest, OrgApp], None]:
    """ Generate mTAN SMS statistics for the given year and month. """

    if date(year, month, 1) >= date.today().replace(day=1):
        abort('Year and month needs to be fully in the past')

    def mtan_statistics(request: OrgRequest, app: OrgApp) -> None:
        mtan_count: int = request.session.query(
            func.count(TAN.id)
        ).filter(and_(
            func.extract('year', TAN.created) == year,
            func.extract('month', TAN.created) == month,
            TAN.meta['mobile_number'].isnot(None)
        )).scalar()
        if mtan_count:
            org_name = app.org.name if hasattr(app, 'org') else None
            title = f'{org_name} ({app.schema})' if org_name else app.schema
            click.echo(
                f'{title}: '
                f'Sent {mtan_count} mTAN SMS'
            )

    return mtan_statistics


@cli.command(name='correct-submission-definitions')
@pass_group_context
def correct_definition_for_submissions(
    group_context: GroupContext
) -> Callable[[OrgRequest, OrgApp], None]:
    """
    ogc-2315 Correct definition of submissions for resource
    `Singsaal Sunnegrund 4` for Steinhausen.
    """

    def correct_submission_definition(
        request: OrgRequest,
        app: OrgApp
    ) -> None:

        from onegov.form import FormSubmission

        patterns = [
            (r'\[ \] Stühle  Anzahl  Bemerkungen = ...',
             r'[ ] Stühle Anzahl Bemerkungen'),
            (r'\[ \] Esstische  Anzahl Bemerkungen = ...',
             r'[ ] Esstische Anzahl Bemerkungen'),
        ]

        session = request.session
        query = session.query(FormSubmission).filter(
            FormSubmission.definition.like(
                '%Stühle  Anzahl  Bemerkungen = ...%') |
            FormSubmission.definition.like(
                '%Esstische  Anzahl Bemerkungen = ...%')
        )
        count = query.count()

        for submission in query.all():
            for pattern, repl in patterns:
                if re.search(pattern, submission.definition):
                    submission.definition = (
                        re.sub(pattern, repl, submission.definition))
                    click.echo(
                        f'Correct pattern in submission id {submission.id}')

        click.echo(f'Corrected {count} submissions')
        session.flush()

    return correct_submission_definition


@cli.command(name='correct-submission-definitions-2')
def correct_definition_for_submissions_2(
) -> Callable[[OrgRequest, OrgApp], None]:
    """
    ogc-2315 Correct definition of submissions for resource
    `Singsaal Sunnegrund 4` for Steinhausen.

    Round 2: Also `Anzahl und Bemerkungen` need to be removed.
    """

    def correct_submission_definition(
        request: OrgRequest,
        app: OrgApp
    ) -> None:

        from onegov.form import FormSubmission

        patterns = [
            (r'\[ \] Stühle Anzahl Bemerkungen', r'[ ] Stühle'),
            (r'\[ \] Esstische Anzahl Bemerkungen', r'[ ] Esstische'),
        ]

        session = request.session
        query = session.query(FormSubmission).filter(
            FormSubmission.definition.like(
                '%Stühle Anzahl Bemerkungen%') |
            FormSubmission.definition.like(
                '%Esstische Anzahl Bemerkungen%')
        )
        count = query.count()

        for submission in query.all():
            for pattern, repl in patterns:
                if re.search(pattern, submission.definition):
                    submission.definition = (
                        re.sub(pattern, repl, submission.definition))
                    click.echo(
                        f'Correct pattern in submission id {submission.id}')

        click.echo(f'Corrected {count} submissions')
        session.flush()

    return correct_submission_definition
