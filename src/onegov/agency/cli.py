from __future__ import annotations

import click
import transaction

from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.data_import import (import_bs_data,
                                       import_membership_titles,
                                       import_lu_data)
from onegov.agency.excel_export import export_person_xlsx
from onegov.agency.models import ExtendedAgencyMembership, ExtendedPerson
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.people import Agency, Person, AgencyMembership
from sqlalchemy import text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.agency.app import AgencyApp
    from onegov.agency.request import AgencyRequest
    from onegov.core.cli.core import GroupContext
    from sqlalchemy.orm import Session

cli = command_group()


@cli.command('consolidate', context_settings={'singular': True})
@click.option('--based-on', required=True, default='email')
@click.option('--ignore_case', is_flag=True, required=True, default=True)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--verbose', is_flag=True, default=False, help='Verbose mode')
def consolidate_cli(
    based_on: str,
    ignore_case: bool,
    dry_run: bool,
    verbose: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:
    """
    Consolidates double entries of person objects based on the property
    `based_on`. Property must be convertible to string.
    """

    def find_double_entries(session: Session) -> tuple[
        dict[str, ExtendedPerson],
        dict[str, list[ExtendedPerson]]
    ]:
        seen: dict[str, ExtendedPerson] = {}
        to_consolidate: dict[str, list[ExtendedPerson]] = {}
        for person in session.query(ExtendedPerson):
            identifier = getattr(person, based_on)
            if not identifier:
                continue
            identifier = str(identifier)
            id_mod = identifier.lower() if ignore_case else identifier

            if id_mod in seen:
                to_remove = to_consolidate.setdefault(id_mod, [])
                to_remove.append(person)
            else:
                seen[id_mod] = person
        return seen, to_consolidate

    def consolidate_persons(
        person: ExtendedPerson,
        persons: list[ExtendedPerson],
        identifier: str
    ) -> ExtendedPerson:
        """Consolidates person with persons on their attributes,
        completing person arg. The identifier is excluded from comparison"""
        attributes = (
            'salutation', 'academic_title', 'first_name', 'last_name', 'born',
            'profession', 'function', 'political_party', 'parliamentary_group',
            'picture_url', 'email', 'phone', 'phone_direct', 'website',
            'address', 'notes', 'access'
        )
        assert persons
        if not persons:
            return person
        for current in persons:
            for attr in attributes:
                if attr == identifier:
                    continue
                value = getattr(current, attr)
                existing = getattr(person, attr)
                if not existing and value:
                    if verbose:
                        click.echo(f'Setting {person.title}: {attr}={value}')
                    setattr(person, attr, value)
        return person

    def consolidate_memberships(
        session: Session,
        person: ExtendedPerson,
        persons: list[ExtendedPerson]
    ) -> None:
        assert person not in persons
        for p in persons:
            for membership in p.memberships:
                membership.person_id = person.id
                session.flush()
            session.delete(p)

    def do_consolidate(request: AgencyRequest, app: AgencyApp) -> None:
        app.fts_orm_events.max_queue_size = 0
        session = request.session
        first_seen, to_consolidate = find_double_entries(session)
        click.echo(f'Double entries found based on '
                   f'{based_on}: {len(to_consolidate)}')
        count = session.query(ExtendedAgencyMembership).count()
        for ix, (id_, persons) in enumerate(to_consolidate.items()):
            person = first_seen[id_]
            person = consolidate_persons(person, persons, id_)
            session.flush()
            consolidate_memberships(session, person, persons)
        count_after = session.query(ExtendedAgencyMembership).count()
        assert count == count_after, f'before: {count}, after {count_after}'
        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

    return do_consolidate


@cli.command('import-bs-membership-title', context_settings={'singular': True})
@click.argument('agency-file', type=click.Path(exists=True))
@click.argument('people-file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, default=False)
def import_bs_function(
    agency_file: str,
    people_file: str,
    dry_run: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:

    def execute(request: AgencyRequest, app: AgencyApp) -> None:
        import_membership_titles(agency_file, people_file, request, app)

        total_empty_titles = 0

        for membership in request.session.query(ExtendedAgencyMembership):
            title = membership.title
            if not title.strip():
                membership.title = 'Mitglied'
                total_empty_titles += 1

        click.echo(f'Corrected remaining empty titles: {total_empty_titles}')

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')
    return execute


@cli.command('import-bs-data', context_settings={'singular': True})
@click.argument('agency-file', type=click.Path(exists=True))
@click.argument('people-file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--clean', is_flag=True, default=False)
def import_bs_data_files(
    agency_file: str,
    people_file: str,
    dry_run: bool,
    clean: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:
    """

    Usage:

        onegov-agency  --select /onegov_agency/bs import-bs-data \
        $agency_file $people_file
    """

    def execute(request: AgencyRequest, app: AgencyApp) -> None:

        if clean:
            session = request.session
            for ix, membership in enumerate(session.query(AgencyMembership)):
                session.delete(membership)

            for ix, person in enumerate(session.query(Person)):
                session.delete(person)

            for ix, agency in enumerate(session.query(Agency)):
                session.delete(agency)

            session.flush()
            click.secho(
                'All Memberships, Agencies and Persons removed', fg='green')
            click.secho('Exiting...')
            return

        agencies, people = import_bs_data(
            agency_file, people_file, request, app)

        click.secho(f'Imported {len(agencies.keys())} agencies '
                    f'and {len(people)} persons',
                    fg='green')
        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

    return execute


@cli.command('import-lu-data', context_settings={'singular': True})
@click.argument('data-file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--clean', is_flag=True, default=False)
def import_lu_data_files(
    data_file: str,
    dry_run: bool,
    clean: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:
    """

    Usage:

        onegov-agency --select /onegov_agency/lu import-lu-data $people_file
    """

    def execute(request: AgencyRequest, app: AgencyApp) -> None:
        if clean:
            schema = app.session_manager.current_schema
            assert schema is not None

            click.secho(f'Cleaning data in schema: {schema}', fg='yellow')

            session = request.session
            agency_count = session.execute(
                text('SELECT COUNT(*) FROM agencies')
            ).scalar()
            people_count = session.execute(
                text('SELECT COUNT(*) FROM people')
            ).scalar()

            click.secho(
                f'Removing {agency_count} Agencies and {people_count} '
                f'Persons from database',
                fg='green'
            )
            request.session.execute(
                text("""
                    TRUNCATE TABLE agencies CASCADE;
                    TRUNCATE TABLE people CASCADE;
                    COMMIT;
                """)
            )
            session.flush()
            if app.fts_search_enabled:
                # remove the relevant entries from the search index
                session.execute(text("""
                    DELETE
                      FROM search_index
                     WHERE owner_tablename IN ('agencies', 'people');
                    COMMIT;
                """))

            click.secho('Exiting...', fg='green')
            return

        agencies, people = import_lu_data(data_file, request, app)
        click.secho(f'Imported {len(people)} persons and '
                    f'{len(agencies)} agencies', fg='green')

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

    return execute


@cli.command('create-pdf')
@pass_group_context
@click.option('--root/--no-root', default=True)
@click.option('--recursive/--no-recursive', default=True)
def create_pdf(
    group_context: GroupContext,
    root: bool,
    recursive: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:

    def _create_pdf(request: AgencyRequest, app: AgencyApp) -> None:
        session = app.session()
        agencies = ExtendedAgencyCollection(session)

        if root:
            app.root_pdf = app.pdf_class.from_agencies(
                agencies=agencies.roots,
                title=app.org.name,
                toc=True,
                exclude=app.org.hidden_people_fields,
                page_break_on_level=int(app.org.meta.get(
                    'page_break_on_level_root_pdf', 1)),
                link_color=app.org.meta.get('pdf_link_color'),
                underline_links=app.org.meta.get('pdf_underline_links', False)
            )

            click.secho('Root PDF created', fg='green')

        if recursive:
            for agency in agencies.query():
                agency.pdf_file = app.pdf_class.from_agencies(
                    agencies=[agency],
                    title=agency.title,
                    toc=False,
                    exclude=app.org.hidden_people_fields,
                    page_break_on_level=int(app.org.meta.get(
                        'page_break_on_level_org_pdf', 1)),
                    link_color=app.org.meta.get('pdf_link_color'),
                    underline_links=app.org.meta.get(
                        'pdf_underline_links', False)
                )
                click.secho(f"Created PDF of '{agency.title}'", fg='green')

    return _create_pdf


@cli.command('export-xlsx')
@pass_group_context
@click.option('--people', default=True, is_flag=True)
def export_xlsx(
    group_context: GroupContext,
    people: bool
) -> Callable[[AgencyRequest, AgencyApp], None]:

    def _export_xlsx(request: AgencyRequest, app: AgencyApp) -> None:
        session = app.session()
        if people:
            xlsx = export_person_xlsx(session)
            app.people_xlsx = xlsx
            click.secho("Created XLSX for people'", fg='green')
    return _export_xlsx


@cli.command('enable-yubikey')
@pass_group_context
def enable_yubikey(
    group_context: GroupContext
) -> Callable[[AgencyRequest, AgencyApp], None]:

    def _enable_yubikey(request: AgencyRequest, app: AgencyApp) -> None:
        if app.org:
            app.org.meta['enable_yubikey'] = True
            click.secho('YubiKey enabled', fg='green')

    return _enable_yubikey


@cli.command('disable-yubikey')
@pass_group_context
def disable_yubikey(
    group_context: GroupContext
) -> Callable[[AgencyRequest, AgencyApp], None]:

    def _disable_yubikey(request: AgencyRequest, app: AgencyApp) -> None:
        if app.org:
            app.org.meta['enable_yubikey'] = False
            click.secho('YubiKey disabled', fg='green')

    return _disable_yubikey
