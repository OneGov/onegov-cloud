from __future__ import annotations

import click
import transaction

from onegov.core.cli import command_group
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory import log
from onegov.translator_directory.models.language import Language
from onegov.translator_directory.utils import (
    update_drive_distances, geocode_translator_addresses)
from onegov.user import User
from onegov.user.auth.clients import LDAPClient
from onegov.user.auth.provider import ensure_user
from onegov.user.sync import ZugUserSource
from sqlalchemy import or_, and_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from ldap3.core.connection import Connection as LDAPConnection
    from onegov.translator_directory.app import TranslatorDirectoryApp
    from onegov.translator_directory.request import TranslatorAppRequest
    from sqlalchemy.orm import Session
    from uuid import UUID


cli = command_group()


def fetch_users(
    app: TranslatorDirectoryApp,
    session: Session,
    ldap_server: str,
    ldap_username: str,
    ldap_password: str,
    admin_group: str,
    editor_group: str,
    verbose: bool = False,
    skip_deactivate: bool = False,
    dry_run: bool = False
) -> None:
    """ Implements the fetch-users cli command. """

    admin_group = admin_group.lower()
    editor_group = editor_group.lower()

    sources = ZugUserSource.factory(verbose=verbose)

    translator_coll = TranslatorCollection(app, user_role='admin')
    translators = {translator.email for translator in translator_coll.query()}

    def users(connection: LDAPConnection) -> Iterator[dict[str, Any]]:
        for src in sources:
            for base, search_filter, attrs in src.bases_filters_attributes:
                success = connection.search(
                    base, search_filter, attributes=attrs
                )
                if not success:
                    log.error('Error importing events', exc_info=True)
                    raise RuntimeError(
                        f"Could not query '{base}' "
                        f"with filter '{search_filter}'"
                    )

                yield from src.map_entries(
                    connection.entries,
                    admin_group=admin_group,
                    editor_group=editor_group,
                    base=base,
                    search_filter=search_filter
                )

    def handle_inactive(synced_ids: list[UUID]) -> None:
        inactive = session.query(User).filter(
            and_(
                User.id.notin_(synced_ids),
                or_(
                    User.source == 'ldap',
                    User.role == 'member'
                )
            )
        )
        for user_ in inactive:
            if user_.active:
                log.info(f'Deactivating inactive user {user_.username}')
            user_.active = False

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()
    count = 0
    synced_users = []
    for data in users(client.connection):

        if data['mail'] in translators:
            log.info(f'Skipping {data["mail"]}, translator exists')
            continue

        if data['type'] == 'ldap':
            source = 'ldap'
            source_id = data['source_id']
            force_role = True
        elif data['type'] == 'regular':
            source = None
            source_id = None
            force_role = False
        else:
            log.error('Unknown auth provider', exc_info=False)
            raise NotImplementedError()

        user = ensure_user(
            source=source,
            source_id=source_id,
            session=session,
            username=data['mail'],
            role=data['role'],
            force_role=force_role,
            force_active=True
        )

        synced_users.append(user.id)

        count += 1

    log.info(f'Synchronized {count} users')

    if not skip_deactivate:
        handle_inactive(synced_users)

    if dry_run:
        transaction.abort()


@cli.command(name='fetch-users', context_settings={'singular': True})
@click.option('--ldap-server', required=True)
@click.option('--ldap-username', required=True)
@click.option('--ldap-password', required=True)
@click.option('--admin-group', required=True, help='group id for role admin')
@click.option('--editor-group', required=True, help='group id for role editor')
@click.option('--verbose', is_flag=True, default=False)
@click.option('--skip-deactivate', is_flag=True, default=False)
@click.option('--dry-run', is_flag=True, default=False)
def fetch_users_cli(
    ldap_server: str,
    ldap_username: str,
    ldap_password: str,
    admin_group: str,
    editor_group: str,
    verbose: bool,
    skip_deactivate: bool,
    dry_run: bool
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:
    r""" Updates the list of users by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:
    .. code-block:: bash

        onegov-translator --select /translator_directory/zug fetch-users \
            --ldap-server 'ldaps://1.2.3.4' \
            --ldap-username 'foo' \
            --ldap-password 'bar' \
            --admin-group 'ou=Admins' \
            --editor-group 'ou=Editors'

    """

    def execute(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:

        fetch_users(
            app,
            request.session,
            ldap_server,
            ldap_username,
            ldap_password,
            admin_group,
            editor_group,
            verbose,
            skip_deactivate,
            dry_run
        )

    return execute


@cli.command(name='update-drive-distance', context_settings={'singular': True})
@click.option('--dry-run/-no-dry-run', default=False)
@click.option('--only-empty/--all', default=True)
@click.option(
    '--tolerance-factor',
    help='Do not overwrite existing distances if off by +- a factor',
    default=0.3,
    type=float
)
@click.option(
    '--max-tolerance',
    type=int,
    help='Tolerate this maximum deviation (km) from an old saved distance',
    default=15
)
@click.option(
    '--max-distance',
    type=int,
    help='Do accept routes longer than this distance (km)',
    default=300
)
def drive_distances_cli(
    dry_run: bool,
    only_empty: bool,
    tolerance_factor: float,
    max_tolerance: int,
    max_distance: int
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:

    def get_distances(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:

        tot, routes_found, _distance_changed, no_routes, tolerance_failed = (
            update_drive_distances(
                request,
                only_empty,
                tolerance_factor,
                max_tolerance,
                max_distance
            )
        )

        click.secho(f'Directions not found: {len(no_routes)}/{tot}',
                    fg='yellow')

        click.secho(f'Over tolerance: {len(tolerance_failed)}/{routes_found}',
                    fg='yellow')

        if no_routes:
            click.secho(
                'Listing all translators whose directions could not be found')
            for trs in no_routes:
                click.secho(f'- {request.link(trs, name="edit")}')

        if tolerance_failed:
            click.secho(
                'Listing all translators who failed distance check')

            for trs, new_dist in tolerance_failed:
                click.secho(f'- {request.link(trs, name="edit")}')
                click.secho(f'  old: {trs.drive_distance}; new: {new_dist}')

        if dry_run:
            transaction.abort()

    return get_distances


@cli.command(name='geocode', context_settings={'singular': True})
@click.option('--dry-run/-no-dry-run', default=False)
@click.option('--only-empty/--all', default=True)
def geocode_cli(
    dry_run: bool,
    only_empty: bool
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:

    def do_geocode(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:

        if not app.mapbox_token:
            click.secho('No mapbox token found, aborting...', fg='yellow')
            return

        trs_total, total, geocoded, skipped, not_found = (
            geocode_translator_addresses(
                request, only_empty,
                bbox=None
            )
        )

        click.secho(f'{total} translators of {trs_total} have an address')
        click.secho(f'Changed: {geocoded}/{total - skipped}, '
                    f'skipped: {skipped}/{total}',
                    fg='green')
        click.secho(f'Coordinates not found: '
                    f'{len(not_found)}/{total - skipped}',
                    fg='yellow')

        click.secho('Listing all translators whose address could not be found')
        for trs in not_found:
            click.secho(f'- {request.link(trs, name="edit")}')

        if dry_run:
            transaction.abort()

    return do_geocode


@cli.command(name='update-accounts', context_settings={'singular': True})
@click.option('--dry-run/-no-dry-run', default=False)
def update_accounts_cli(
    dry_run: bool
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:
    """ Updates user accounts for translators. """

    def do_update_accounts(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:

        translators = TranslatorCollection(request.app, user_role='admin')
        for translator in translators.query():
            translators.update_user(translator, translator.email)

        if dry_run:
            transaction.abort()

    return do_update_accounts


LANGUAGES = (
    'Afrikaans',
    'Albanisch',
    'Amharisch',
    'Anyin',
    'Arabisch',
    'Arabisch (Dialekte)',
    'Arabisch (Hocharabisch)',
    'Arabisch (Masri)',
    'Arabisch (Nahost)',
    'Aramäisch',
    'Armenisch',
    'Aserbaidschanisch',
    'Badini',
    'Bangla',
    'Bengalisch',
    'Bilen',
    'Bosnisch',
    'Bulgarisch',
    'Chinesisch',
    'Chinesisch (Hokkien)',
    'Chinesisch (Mandarin)',
    'Dänisch',
    'Dari',
    'Dari (Afghanistan)',
    'Deutsch',
    'Diola',
    'Edo',
    'Englisch',
    'Ewe',
    'Farsi',
    'Farsi (Persisch)',
    'Farsi Persisch (Afghanistan Iran)',
    'Flämisch',
    'Französisch',
    'Friesisch',
    'Galicisch',
    'Gebärdensprache',
    'Georgisch',
    'Griechisch',
    'Gujarati',
    'Hebräisch',
    'Hindi',
    'Ibo',
    'Igbo',
    'Ijaw',
    'Indonesisch',
    'Irakisch',
    'Iranisch',
    'Italienisch',
    'Italienisch (Dialekte Süditalien)',
    'Itsekiri',
    'Japanisch',
    'Kabyé',
    'Kalabari',
    'Kantonesisch',
    'Kasachisch',
    'Keine schriftlichen Übersetzungen',
    'Keine Verdolmetschung',
    'Kotokoli',
    'Kreolisch',
    'Kroatisch',
    'Kurdisch',
    'Kurdisch (Dialekte)',
    'Kurmanci',
    'Kyrillisch (Serbien)',
    'Lettisch',
    'Litauisch',
    'Mandarin',
    'Mandinka',
    'Marathi',
    'Marokkanisch',
    'Mazedonisch',
    'Mina',
    'Moldauisch',
    'Mongolisch',
    'Montenegrinisch',
    'Niederländisch',
    'Oromo',
    'Pakistanisch',
    'Panjabi',
    'Paschto (Afghanistan, Pakistan)',
    'Paschtu',
    'Patois',
    'Persisch',
    'Pidgin',
    'Pidgin-Englisch',
    'Pidgin-Französisch',
    'Pidgin-Nigerianisch',
    'Pilipino',
    'Polnisch',
    'Portugiesisch',
    'Portugiesisch (Brasil)',
    'Punjabi',
    'Rumänisch',
    'Russisch',
    'Schwedisch',
    'Serbisch',
    'Serbokroatisch',
    'Shandong-Dialekt',
    'Shanghai-Dialekt',
    'Singhalesisch',
    'Slowakisch',
    'Somali',
    'Sorani',
    'Spanisch',
    'Suaheli',
    'Tadschikisch',
    'Tagalog',
    'Tamil',
    'Tamilisch',
    'Telugu',
    'Tem',
    'Thailändisch',
    'Tibetisch',
    'Tigrinya',
    'Tschechisch',
    'Türkisch',
    'Türkisch (Dialekte)',
    'Turkmenisch',
    'Uigurisch',
    'Ukrainisch',
    'Ungarisch',
    'Urdu',
    'Usbekisch',
    'VG ZG',
    'Vietnamesisch',
    'Weissrussisch',
    'Wolof',
    'Yoruba',
    'Yue-Chinesisch'
)


@cli.command(name='create-languages', context_settings={'singular': True})
@click.option('--dry-run', is_flag=True, default=False)
def create_languages(
        dry_run: bool
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:
    """
    Create languages for the selected translator schema. Languages get
    created if they don't exist to prevent id changes.

    This command is useful when new languages were added to the LANGUAGES list.

    NOTE: No language will be deleted. If a language is not in the LANGUAGES
    list the script will print a message.

    Example:
        onegov-translator --select /translator_directory/schaffhausen
        create-languages --dry-run
    """

    def do_create_languages(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:
        # Compare existing languages
        existing = request.session.query(Language).all()
        existing_lang_names = [lang.name for lang in existing]
        for language in existing:
            if language.name not in LANGUAGES:
                click.secho(f"Language '{language.name}' is "
                            f'unknown. You may delete it if not in use from '
                            f"'/languages'", fg='yellow')

        # create languages if not existing (to prevent id changes)
        add_count = 0
        for language_name in LANGUAGES:
            if language_name not in existing_lang_names:
                add_count += 1
                lang = Language(name=language_name)
                request.session.add(lang)
        click.secho(f'Inserted {add_count} languages of total '
                    f'{len(LANGUAGES)}', fg='green')

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')
        else:
            request.session.flush()

    return do_create_languages


@cli.command(name='force-delete-languages',
             context_settings={'singular': True})
@click.option('--dry-run', is_flag=True, default=False)
def force_delete_languages(
        dry_run: bool
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:
    """
    This command forcefully deletes all languages from the database and all
    references will be lost.
    This command is useful after the languages have changed and
    assigned a lot for testing.

    Example:
        onegov-translator --select /translator_directory/schaffhausen
        delete-languages --dry-run
    """

    def do_delete_languages(
        request: TranslatorAppRequest,
        app: TranslatorDirectoryApp
    ) -> None:

        i = input('Are you sure you want to delete all languages and losing '
                  'all references to it? [y/N]: ')
        if i.lower() != 'y':
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')
            return

        del_count = 0
        languages = request.session.query(Language)
        for lang in languages:
            del_count += 1
            request.session.delete(lang)
        click.secho(f'Deleted {del_count} languages', fg='green')

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')
        else:
            request.session.flush()

    return do_delete_languages


@cli.command(
    name='recalculate-travel-details', context_settings={'singular': True}
)
@click.option('--dry-run/-no-dry-run', default=False)
@click.option(
    '--status',
    type=click.Choice(['pending', 'confirmed', 'all']),
    default='all',
    help='Which reports to fix',
)
def recalculate_travel_details_cli(
    dry_run: bool, status: str
) -> Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]:
    r"""Recalculate travel compensation and distance for open time reports.

    This fixes incorrect travel calculations due to old logic errors.
    Only updates reports that have not yet been exported to accounting.

    Example:
        onegov-translator --select /translator_directory/zug \
            recalculate-travel-details --dry-run
    """

    def do_recalculate(
        request: TranslatorAppRequest, app: TranslatorDirectoryApp
    ) -> None:
        from decimal import Decimal
        from onegov.translator_directory.models.time_report import (
            TranslatorTimeReport,
        )
        from onegov.translator_directory.utils import (
            calculate_distance_to_location,
        )

        # Query open time reports (not exported)
        query = request.session.query(TranslatorTimeReport).filter(
            TranslatorTimeReport.exported == False
        )

        # Filter by status if specified
        if status == 'pending':
            query = query.filter(TranslatorTimeReport.status == 'pending')
        elif status == 'confirmed':
            query = query.filter(TranslatorTimeReport.status == 'confirmed')

        reports = query.all()
        updated_count = 0
        skipped_count = 0

        click.secho(f'Processing {len(reports)} time reports...', fg='blue')

        for report in reports:
            translator = report.translator
            if not translator:
                click.secho(
                    f'Skipping report {report.id}: translator not found',
                    fg='yellow',
                )
                skipped_count += 1
                continue

            # Calculate travel details
            compensation = Decimal('0')
            distance = None

            # Skip travel calculation if requested
            if report.assignment_type == 'on-site':
                one_way_km = None

                # Try to calculate distance if we have coordinates
                if translator.coordinates:
                    location_key = report.assignment_location or ''
                    one_way_km = calculate_distance_to_location(
                        request, translator.coordinates, location_key, None
                    )

                # Fall back to translator's drive_distance
                if one_way_km is None and translator.drive_distance:
                    one_way_km = float(translator.drive_distance)

                # Calculate compensation based on distance tiers
                if one_way_km is not None:
                    distance = one_way_km
                    if one_way_km <= 25:
                        compensation = Decimal('20')
                    elif one_way_km <= 50:
                        compensation = Decimal('50')
                    elif one_way_km <= 100:
                        compensation = Decimal('100')
                    else:
                        compensation = Decimal('150')

            # Update the report
            old_comp = report.travel_compensation
            old_dist = report.travel_distance
            report.travel_compensation = compensation
            report.travel_distance = distance

            # Recalculate total compensation
            breakdown = report.calculate_compensation_breakdown()
            report.total_compensation = breakdown['total']

            if old_comp != compensation or old_dist != distance:
                click.secho(
                    f'✓ {translator.title}: '
                    f'comp {old_comp}→{compensation}, '
                    f'dist {old_dist}→{distance}',
                    fg='green',
                )
                updated_count += 1
            else:
                skipped_count += 1

        click.secho(f'Updated: {updated_count}/{len(reports)}', fg='green')

        if dry_run:
            transaction.abort()
            click.secho('Dry run: transaction aborted', fg='yellow')
        else:
            request.session.flush()
            click.secho('Changes committed', fg='green')

    return do_recalculate
