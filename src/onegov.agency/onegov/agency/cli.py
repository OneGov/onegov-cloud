import click
import re
import transaction

from io import BytesIO
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.pdf import AgencyPdf
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.people.collections import AgencyCollection
from onegov.people.collections import PersonCollection
from onegov.people.models import AgencyMembership
from requests import get
from textwrap import indent
from xlrd import open_workbook

cli = command_group()


@cli.command('import-agencies')
@click.argument('file', type=click.Path(exists=True))
@click.option('--clear/--no-clear', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--visualize/--no-visualize', default=False)
@pass_group_context
def import_agencies(group_context, file, clear, dry_run, visualize):
    """ Import data from a seantis.agencies export. For example:

        onegov-people \
            --select '/towns/govikon' \
            import-agencies export-agencies.xlsx

    """

    def _import(request, app):
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
        parents = {}
        alphabetical = []
        for row in range(1, sheet.nrows):
            id_ = int(sheet.cell_value(row, 0))
            agency = agencies.add(
                id=id_,
                parent=parents.get(id_),
                title=sheet.cell_value(row, 2).strip(),
                description=sheet.cell_value(row, 3).strip(),
                portrait=sheet.cell_value(row, 4).strip(),
                export_fields=sheet.cell_value(row, 7),
                state=sheet.cell_value(row, 8),
                order=id_,
            )

            organigram_url = sheet.cell_value(row, 6)
            if organigram_url:
                response = get(organigram_url)
                response.raise_for_status()
                agency.organigram = BytesIO(response.content)

            if sheet.cell_value(row, 5):
                alphabetical.append(id_)

            for child in sheet.cell_value(row, 1).split(','):
                parents[int(child or -1)] = agency

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
            person = people.add(
                academic_title=sheet.cell_value(row, 0).strip(),
                profession=sheet.cell_value(row, 1).strip(),
                first_name=sheet.cell_value(row, 2).strip(),
                last_name=sheet.cell_value(row, 3).strip(),
                political_party=sheet.cell_value(row, 4).strip(),
                year=sheet.cell_value(row, 5).strip(),
                email=sheet.cell_value(row, 6).strip(),
                address=sheet.cell_value(row, 7).strip(),
                phone=sheet.cell_value(row, 8).strip(),
                direct_phone=sheet.cell_value(row, 9).strip(),
                salutation=sheet.cell_value(row, 10).strip(),
                website=sheet.cell_value(row, 12).strip(),
                keywords=sheet.cell_value(row, 13).strip(),
                notes=sheet.cell_value(row, 14).strip(),
            )
            memberships = sheet.cell_value(row, 15).split('//')
            for membership in memberships:
                if membership:
                    values = re.match(
                        r'^\((\d*)\)\((.*)\)\((.*)\)\((.*)\)\((\d*)\)$',
                        membership
                    ).groups()
                    person.memberships.append(
                        AgencyMembership(
                            agency_id=int(values[0]),
                            title=values[1] or "",
                            since=values[2] or None,
                            order=int(values[4]),
                            meta={
                                'prefix': values[3],
                            }
                        )
                    )

        for id_ in alphabetical:
            agencies.by_id(id_).sort_relationships()

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

        if dry_run:
            transaction.abort()
            click.secho("Aborting transaction", fg='yellow')

    return _import


@cli.command('export-pdf')
@pass_group_context
@click.option('--recursive  /--no-recursive', default=True)
def export_pdf(group_context):

    def _export_pdf(request, app):
        session = app.session()
        agencies = ExtendedAgencyCollection(session)

        # pdf = AgencyPdf.from_agencies(
        #     agencies.roots,
        #     "Kanton Zug",
        #      title="Staatskalender Kanton Zug",
        #      toc=True
        # )
        # with open('out/_full.pdf', 'wb') as file:
        #     file.write(pdf.read())

        for agency in agencies.query():
            agency.pdf = AgencyPdf.from_agencies([agency], 'Kanton Zug')
            click.secho(f"Created PDF of '{agency.title}'", fg='green')

    return _export_pdf
