import click
import transaction

from collections import OrderedDict
from onegov.core.cli import command_group
from onegov.core.cli import abort
from onegov.people.models import Person
from openpyxl import load_workbook
from openpyxl import Workbook


cli = command_group()


@cli.command('clear')
@click.option('--dry-run/--no-dry-run', default=False)
def clear(dry_run):
    """ Deletes all people.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/town/govikon' clear

    """

    def _clear(request, app):
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
    ('Webseite', 'website'),
    ('Adresse', 'address'),
    ('Link zum Bild', 'picture_url'),
    ('Notizen', 'notes'),
))


@cli.command('export')
@click.argument('filename', type=click.Path(exists=False))
def export_xlsx(filename):
    """ Exports all people to an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/town/govikon' export people.xlsx

    """

    def _export(request, app):
        session = app.session()

        book = Workbook()
        book.remove(book.active)

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
def import_xlsx(file):
    """ Imports people from an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/town/govikon' import people.xlsx

    """

    def _import(request, app):
        session = app.session()

        book = load_workbook(file)

        click.secho('Importing people', fg='yellow')
        sheet = book['Personen']
        count = 0
        for index, row in enumerate(sheet.rows):
            values = tuple(cell.value for cell in row)
            if not index:
                assert values == tuple(EXPORT_FIELDS.keys())
            else:
                session.add(
                    Person(**dict(zip(EXPORT_FIELDS.values(), values)))
                )
                count += 1

        click.secho(f'Imported {count} person(s)', fg='green')

    return _import
