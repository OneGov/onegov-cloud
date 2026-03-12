from __future__ import annotations

import sys

import click
import transaction

from collections import OrderedDict

from onegov.core.cli import command_group
from onegov.core.cli import abort
from onegov.people.models import Person
from openpyxl import load_workbook
from openpyxl import Workbook


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest


cli = command_group()


@cli.command('clear')
@click.option('--dry-run/--no-dry-run', default=False)
def clear(dry_run: bool) -> Callable[[CoreRequest, Framework], None]:
    """ Deletes all people.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/org/govikon' clear

    """

    def _clear(request: CoreRequest, app: Framework) -> None:
        if not click.confirm('Do you really want to remove all people?'):
            abort('Deletion process aborted')

        session = app.session()

        click.secho('Deleting people', fg='yellow')
        count = 0
        for person in session.query(Person):
            session.delete(person)
            count += 1

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

        click.secho(f'Deleted {count} person(s)', fg='green')

    return _clear


EXPORT_FIELDS = OrderedDict((
    ('Anrede', 'salutation'),
    ('Akademischer Titel', 'academic_title'),
    ('Vorname', 'first_name'),
    ('Nachname', 'last_name'),
    ('Funktion', 'function'),
    ('E-Mail', 'email'),
    ('Telefon', 'phone'),
    ('Direktnummer', 'phone_direct'),
    ('Geboren', 'born'),
    ('Beruf', 'profession'),
    ('Politische Partei', 'political_party'),
    ('Fraktion', 'parliamentary_group'),
    ('Organisation', 'organisation'),
    ('Unterorganisation', 'sub_organisation'),
    ('Webseite', 'website'),
    ('Webseite 2', 'website_2'),
    ('Standort Adresse', 'location_address'),
    ('Standort Postleitzahl und Ort', 'location_code_city'),
    ('Postadresse', 'postal_address'),
    ('Postleitzahl und Ort', 'postal_code_city'),
    ('Link zum Bild', 'picture_url'),
    ('Notizen', 'notes'),
))


@cli.command('export')
@click.argument('filename', type=click.Path(exists=False))
def export_xlsx(filename: str) -> Callable[[CoreRequest, Framework], None]:
    """ Exports all people to an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/onegov_org/govikon' export people.xlsx

    """

    def _export(request: CoreRequest, app: Framework) -> None:
        session = app.session()

        book = Workbook()
        book.remove(book.active)  # type:ignore[arg-type]

        click.secho('Exporting people', fg='yellow')
        sheet = book.create_sheet('Personen')
        sheet.append(tuple(EXPORT_FIELDS.keys()))
        count = 0
        for person in session.query(Person):
            sheet.append(
                tuple(getattr(person, attr) for attr in EXPORT_FIELDS.values())
            )
            count += 1

        book.save(filename)

        click.secho(f'Exported {count} person(s)', fg='green')

    return _export


@cli.command('import')
@click.argument('file', type=click.File('rb'))
def import_xlsx(file: IO[bytes]) -> Callable[[CoreRequest, Framework], None]:
    """ Imports people from an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/onegov_org/govikon' import people.xlsx

    """

    def _import(request: CoreRequest, app: Framework) -> None:
        session = app.session()

        book = load_workbook(file)

        click.secho('Importing people', fg='yellow')
        sheet = book['Personen']

        # FIXME: We should probably do this check at runtime eventually
        if TYPE_CHECKING:
            from openpyxl.worksheet.worksheet import Worksheet
            assert isinstance(sheet, Worksheet)

        count = 0
        for index, row in enumerate(sheet.rows):
            values = tuple(cell.value for cell in row)
            if not index:
                if values != tuple(EXPORT_FIELDS.keys()):
                    click.echo('Error in column headers')
                    click.echo('\nExpected - Current')
                    for exp, cur in zip(tuple(EXPORT_FIELDS.keys()), values):
                        color = 'green' if exp == cur else 'red'
                        click.secho(f'{exp} - {cur}', fg=color)
                    sys.exit('\nAborting import')
            else:
                session.add(
                    Person(**dict(zip(EXPORT_FIELDS.values(), values)))
                )
                count += 1

        click.secho(f'Imported {count} person(s)', fg='green')

    return _import


@cli.command('list')
def list_people() -> Callable[[CoreRequest, Framework], None]:

    def _list(request: CoreRequest, app: Framework) -> None:
        session = app.session()
        properties = [
            ('Funktion', 'function'),
            ('Standortadresse', 'location_address', 'location_code_city'),
            ('Postadresse', 'postal_address', 'postal_code_city'),
            ('E-Mail', 'email'),
            ('Telefon', 'phone'),
            ('Telefon direkt', 'phone_direct'),
            ('Telefon intern', 'phone_internal'),
        ]
        for p in session.query(Person):
            click.secho(f'{p.title}', fg='green')
            for label, *prop in properties:
                value = ', '.join(
                    value
                    for attr in prop
                    if (raw_value := getattr(p, attr, None)) is not None
                    if (value := str(raw_value))
                )
                if value:
                    click.secho(f'  {label}: {value}')

            click.secho()

    return _list
