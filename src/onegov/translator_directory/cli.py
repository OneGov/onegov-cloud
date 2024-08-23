import re

import click
import transaction

from onegov.core.cli import command_group
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory import log
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.utils import (
    update_drive_distances, geocode_translator_addresses, country_code_to_name)
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
    app: 'TranslatorDirectoryApp',
    session: 'Session',
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

    def users(connection: 'LDAPConnection') -> 'Iterator[dict[str, Any]]':
        for src in sources:
            for base, search_filter, attrs in src.bases_filters_attributes:
                success = connection.search(
                    base, search_filter, attributes=attrs
                )
                if not success:
                    log.error("Error importing events", exc_info=True)
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

    def handle_inactive(synced_ids: list['UUID']) -> None:
        inactive = session.query(User).filter(
            and_(
                User.id.notin_(synced_ids),
                or_(
                    User.source == 'ldap',
                    User.role == 'member'
                )
            )
        )
        for ix, user_ in enumerate(inactive):
            if user_.active:
                log.info(f'Deactivating inactive user {user_.username}')
            user_.active = False

            if not dry_run:
                if ix % 200 == 0:
                    app.es_indexer.process()
                    app.psql_indexer.bulk_process(session)

    client = LDAPClient(ldap_server, ldap_username, ldap_password)
    client.try_configuration()
    count = 0
    synced_users = []
    for ix, data in enumerate(users(client.connection)):

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
            log.error("Unknown auth provider", exc_info=False)
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
        if not dry_run:
            if ix % 200 == 0:
                session.flush()
                app.es_indexer.process()
                app.psql_indexer.bulk_process(session)

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
) -> 'Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]':
    """ Updates the list of users by fetching matching users
    from a remote LDAP server.

    This is currently highly specific for the Canton of Zug and therefore most
    values are hard-coded.

    Example:

        onegov-translator --select /translator_directory/zug fetch-users \\
            --ldap-server 'ldaps://1.2.3.4' \\
            --ldap-username 'foo' \\
            --ldap-password 'bar' \\
            --admin-group 'ou=Admins' \\
            --editor-group 'ou=Editors'

    """

    def execute(
        request: 'TranslatorAppRequest',
        app: 'TranslatorDirectoryApp'
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
) -> 'Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]':

    def get_distances(
        request: 'TranslatorAppRequest',
        app: 'TranslatorDirectoryApp'
    ) -> None:

        tot, routes_found, distance_changed, no_routes, tolerance_failed = (
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
) -> 'Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]':

    def do_geocode(
        request: 'TranslatorAppRequest',
        app: 'TranslatorDirectoryApp'
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
) -> 'Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]':
    """ Updates user accounts for translators. """

    def do_update_accounts(
        request: 'TranslatorAppRequest',
        app: 'TranslatorDirectoryApp'
    ) -> None:

        translators = TranslatorCollection(request.app, user_role='admin')
        for translator in translators.query():
            translators.update_user(translator, translator.email)

        if dry_run:
            transaction.abort()

    return do_update_accounts


@cli.command(name='migrate-nationalities',
             context_settings={'default_selector': '*'})
@click.option('--dry-run', is_flag=True, default=False)
def migrate_nationalities(
    dry_run: bool
) -> 'Callable[[TranslatorAppRequest, TranslatorDirectoryApp], None]':
    """ Migrates the nationalities column into content column.

    Example:
        onegov-translator
            --select /translator_directory/zug
                migrate-nationalities --dry-run

    """

    def do_migrate_nationalities(
        request: 'TranslatorAppRequest',
        app: 'TranslatorDirectoryApp'
    ) -> None:

        translators = request.session.query(Translator).all()
        not_migrated = 0
        migrated = 0
        auto_mapping = {
            'Grossbritannien': 'GB',
            'Oesterreich': 'AT',
            'Türkei': 'TR',  # babel issue #1112
            'Tibet': 'CN',
        }

        mapping = country_code_to_name(request.locale)
        country_codes = list(mapping.keys())
        country_names = list(mapping.values())
        for translator in translators:
            new = []
            if translator.nationality:
                current = translator.nationality
                if current in country_codes:
                    new.append(current)
                elif current in country_names:
                    country_idx = country_names.index(current)
                    new.append(country_codes[country_idx])
                else:
                    words = re.split(r'\s|,|;|-|\.|\/|\n', current)
                    for word in words:
                        if not word or word == 'migrated':
                            continue
                        if word in country_codes:
                            new.append(word)
                        elif word in country_names:
                            country_idx = country_names.index(word)
                            new.append(country_codes[country_idx])
                        else:
                            if word in auto_mapping:
                                new.append(auto_mapping[word])
                            elif 'Bosnien und Herzegowina' in current:
                                new.append('BA')
                            elif 'Tschechische Republik' in current:
                                new.append('CZ')
                            elif 'Slowakische Republik' in current:
                                new.append('SK')
                            else:
                                click.secho(
                                    f'  Unknown: \'{word}\'', fg='yellow')
                                not_migrated += 1
                                continue

            else:
                pass

            translator.content['nationalities'] = list(set(new))
            translator.nationality = 'migrated'  # type ignore[attr-defined]
            migrated += 1

        if not_migrated:
            click.secho(f'Migration failed for {not_migrated} translator(s) '
                        f'of {len(translators)}')
        else:
            click.secho(f'Migration successful for {migrated} translators')

        if dry_run:
            transaction.abort()
        else:
            request.session.flush()

    return do_migrate_nationalities
