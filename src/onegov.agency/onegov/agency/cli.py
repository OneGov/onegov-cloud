import click
import re
import transaction

from bleach import Cleaner
from html5lib.filters.base import Filter
from html5lib.filters.whitespace import Filter as whitespace_filter
from io import BytesIO
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedAgencyMembership
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.core.html import html_to_text
from onegov.people.collections import AgencyCollection
from onegov.people.collections import PersonCollection
from requests import get
from textwrap import indent
from xlrd import open_workbook


cli = command_group()


@cli.command('import-agencies')
@click.argument('file', type=click.Path(exists=True))
@click.option('--clear/--no-clear', default=True)
@click.option('--skip-root/--no-skip-root', default=True)
@click.option('--skip-download/--no-skip-download', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--visualize/--no-visualize', default=False)
@pass_group_context
def import_agencies(group_context, file, clear, skip_root, skip_download,
                    dry_run, visualize):
    """ Import data from a seantis.agencies export. For example:

        onegov-people \
            --select '/towns/govikon' \
            import-agencies export-agencies.xlsx

    """

    def _import(request, app):
        EXPORT_FIELDS = {
            'academic_title': 'person.academic_title',
            'address': 'person.address',
            'direct_number': 'person.phone_direct',
            'firstname': 'person.first_name',
            'lastname': 'person.last_name',
            'occupation': 'person.profession',
            'phone': 'person.phone',
            'political_party': 'person.political_party',
            'postfix': 'membership.addition',
            'role': 'membership.title',
            'start': 'membership.since',
            'title': 'person.title',
            'year': 'person.born',
        }

        class LinkFilter(Filter):
            """ Uses the href rather than the content of an a-tag. """

            def __iter__(self):
                in_link = False
                for token in Filter.__iter__(self):
                    if token.get('name') == 'a':
                        if token['type'] == 'StartTag':
                            in_link = True
                            data = token['data'][(None, 'href')]
                            data = data.replace('mailto:', '')
                            yield {
                                'type': 'Characters',
                                'data': data
                            }
                        elif token['type'] == 'EndTag':
                            in_link = False
                    elif token['type'] == 'Characters':
                        if not in_link:
                            yield token
                    else:
                        yield token

        cleaner = Cleaner(
            tags=['a', 'p', 'br'],
            attributes={'a': 'href'},
            strip=True,
            filters=[LinkFilter, whitespace_filter]
        )

        session = app.session()

        if clear:
            click.secho("Deleting all agencies", fg='yellow')
            for root in AgencyCollection(session).roots:
                session.delete(root)
            click.secho("Deleting all people", fg='yellow')
            for person in PersonCollection(session).query():
                session.delete(person)

        workbook = open_workbook(file)

        click.secho("Importing agencies", fg='green')
        agencies = ExtendedAgencyCollection(session)
        people = ExtendedPersonCollection(session)
        sheet = workbook.sheet_by_name('Organisationen')
        ids = {}
        parents = {}
        alphabetical = []
        for row in range(1, sheet.nrows):
            if skip_root and row == 1:
                continue

            if row and (row % 50 == 0):
                app.es_indexer.process()

            # We use our own, internal IDs which are auto-incremented
            external_id = int(sheet.cell_value(row, 0))

            # Remove the HTML code from the portrait, prepend the description
            portrait = '\n'.join((
                sheet.cell_value(row, 3).strip(),
                html_to_text(cleaner.clean(sheet.cell_value(row, 4)))
            ))
            portrait = portrait.replace('\n\n', '\n').strip()

            # Re-map the export fields
            export_fields = sheet.cell_value(row, 7) or 'role,title'
            export_fields = export_fields.split(',')
            export_fields = [EXPORT_FIELDS[field] for field in export_fields]

            agency = agencies.add(
                parent=parents.get(external_id),
                title=sheet.cell_value(row, 2).strip(),
                portrait=portrait,
                export_fields=export_fields,
                is_hidden_from_public=sheet.cell_value(row, 8) == 'private',
                order=external_id,
            )
            ids[external_id] = agency.id

            # Download and add the organigram
            if not skip_download:
                organigram_url = sheet.cell_value(row, 6)
                if organigram_url:
                    response = get(organigram_url)
                    response.raise_for_status()
                    agency.organigram_file = BytesIO(response.content)

            if sheet.cell_value(row, 5):
                alphabetical.append(agency.id)

            for child in sheet.cell_value(row, 1).split(','):
                if child:
                    child = int(child)
                    parents[child] = agency

        # Let's make sure, the order have nice, cohere values
        def defrag_ordering(agency):
            for order, child in enumerate(agency.children):
                child.order = order
                defrag_ordering(child)

        for order, root in enumerate(agencies.roots):
            root.order = order
            defrag_ordering(root)

        click.secho("Importing people and memberships", fg='green')
        sheet = workbook.sheet_by_name('Personen')
        for row in range(1, sheet.nrows):
            if row and (row % 50 == 0):
                app.es_indexer.process()

            notes = '\n'.join((
                sheet.cell_value(row, 13).strip(),
                sheet.cell_value(row, 14).strip()
            )).strip()

            person = people.add(
                academic_title=sheet.cell_value(row, 0).strip(),
                profession=sheet.cell_value(row, 1).strip(),
                function=(
                    sheet.cell_value(row, 17).strip()
                    if sheet.ncols > 17 else ''
                ),
                first_name=sheet.cell_value(row, 2).strip(),
                last_name=sheet.cell_value(row, 3).strip(),
                political_party=sheet.cell_value(row, 4).strip(),
                born=sheet.cell_value(row, 5).strip(),
                email=sheet.cell_value(row, 6).strip(),
                address=sheet.cell_value(row, 7).strip(),
                phone=sheet.cell_value(row, 8).strip(),
                phone_direct=sheet.cell_value(row, 9).strip(),
                salutation=sheet.cell_value(row, 10).strip(),
                website=sheet.cell_value(row, 12).strip(),
                is_hidden_from_public=sheet.cell_value(row, 15) == 'private',
                notes=notes,
            )
            memberships = sheet.cell_value(row, 16).split('//')
            for membership in memberships:
                if membership:
                    values = re.match(
                        r'^\((\d*)\)\((.*)\)\((.*)\)\((.*)\)'
                        r'\((.*)\)\((.*)\)\((\d*)\)$',
                        membership
                    ).groups()
                    person.memberships.append(
                        ExtendedAgencyMembership(
                            agency_id=ids[int(values[0])],
                            title=values[1] or "",
                            since=values[2] or None,
                            prefix=values[3],
                            addition=values[4],
                            note=values[5],
                            order=int(values[6]),
                        )
                    )

        # Order the memberships alphabetically, if desired
        for id_ in alphabetical:
            agencies.by_id(id_).sort_relationships()

        # Show a tree view of what we imported
        if visualize:
            click.secho("Imported data:", fg='green')

            def show(agency, level):
                text = f'{agency.title}\n'
                for membership in agency.memberships:
                    person = membership.person
                    text += f'* {membership.title}: {person.title}\n'
                click.echo(indent(text.strip(), level * '  '))

                for child in agency.children:
                    show(child, level + 1)

            for root in agencies.roots:
                show(root, 1)

        # Abort the transaction if requested
        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import


@cli.command('create-pdf')
@pass_group_context
@click.option('--root/--no-root', default=True)
@click.option('--recursive/--no-recursive', default=True)
def create_pdf(group_context, root, recursive):

    def _create_pdf(request, app):
        session = app.session()
        agencies = ExtendedAgencyCollection(session)

        if root:
            app.root_pdf = app.pdf_class.from_agencies(
                agencies=agencies.roots,
                title=app.org.name,
                toc=True,
                exclude=app.org.hidden_people_fields
            )
            click.secho("Root PDF created", fg='green')

        if recursive:
            for agency in agencies.query():
                agency.pdf_file = app.pdf_class.from_agencies(
                    agencies=[agency],
                    title=agency.title,
                    toc=False,
                    exclude=app.org.hidden_people_fields
                )
                click.secho(f"Created PDF of '{agency.title}'", fg='green')

    return _create_pdf


@cli.command('enable-yubikey')
@pass_group_context
def enable_yubikey(group_context):

    def _enable_yubikey(request, app):
        if app.org:
            app.org.meta['enable_yubikey'] = True
            click.secho("YubiKey enabled", fg='green')

    return _enable_yubikey


@cli.command('disable-yubikey')
@pass_group_context
def disable_yubikey(group_context):

    def _disable_yubikey(request, app):
        if app.org:
            app.org.meta['enable_yubikey'] = False
            click.secho("YubiKey disabled", fg='green')

    return _disable_yubikey
