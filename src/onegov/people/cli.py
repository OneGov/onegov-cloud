import click
import re
import transaction

from collections import OrderedDict
from bs4 import BeautifulSoup

from onegov.core.cli import command_group
from onegov.core.cli import abort
from onegov.people import Agency
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
def clear(dry_run: bool) -> 'Callable[[CoreRequest, Framework], None]':
    """ Deletes all people.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/org/govikon' clear

    """

    def _clear(request: 'CoreRequest', app: 'Framework') -> None:
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
def export_xlsx(filename: str) -> 'Callable[[CoreRequest, Framework], None]':
    """ Exports all people to an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/org/govikon' export people.xlsx

    """

    def _export(request: 'CoreRequest', app: 'Framework') -> None:
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
def import_xlsx(file: IO[bytes]) -> 'Callable[[CoreRequest, Framework], None]':
    """ Imports people from an excel file.

    Does not support agencies and memberships at the moment.

    Example:

        onegov-people --select '/org/govikon' import people.xlsx

    """

    def _import(request: 'CoreRequest', app: 'Framework') -> None:
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
                assert values == tuple(EXPORT_FIELDS.keys())
            else:
                session.add(
                    Person(**dict(zip(EXPORT_FIELDS.values(), values)))
                )
                count += 1

        click.secho(f'Imported {count} person(s)', fg='green')

    return _import


p2 = re.compile(r'(.*), (.*)Postadresse: (.*), (.*)')
p3 = re.compile(r'(.*), (Postfach), (.*)')
p4 = re.compile(r'(.*), (.*), (.*)')
p1 = re.compile(r'(.*), (.*)')
p6 = re.compile(r'(.*)\n(.*)')
p5 = re.compile(r'([A-Za-z ]*) ?(\d+[a-z]?)?')  # street name and optional
# building number


def parse_and_split_address_field(address: str) -> tuple[str, str, str, str]:
    """
    Parsing the `address` field to split into location address and code/city
    as well as postal address and code/city.

    :param address:str
    :return: tuple: (location_address, location_code_city,
                     postal_address, postal_code_city)
    """
    location_addr = ''
    location_pcc = ''
    postal_addr = ''
    postal_pcc = ''

    # sanitize address
    if ';' in address:
        address = address.replace('; ', '')
        address = address.replace(';', '')

    if not address:
        return location_addr, location_pcc, postal_addr, postal_pcc

    if m := p2.match(address):
        location_addr = m.group(1)
        location_pcc = m.group(2)
        postal_addr = m.group(3)
        postal_pcc = m.group(4)
        return location_addr, location_pcc, postal_addr, postal_pcc

    if m := p3.match(address):
        postal_addr = m.group(1) + '\n' + m.group(2)
        postal_pcc = m.group(3)
        return location_addr, location_pcc, postal_addr, postal_pcc

    if m := p4.match(address):
        postal_addr = m.group(1) + '\n' + m.group(2)
        postal_pcc = m.group(3)
        return location_addr, location_pcc, postal_addr, postal_pcc

    if m := p1.match(address):
        postal_addr = m.group(1)
        postal_pcc = m.group(2)
        return location_addr, location_pcc, postal_addr, postal_pcc

    if p6.match(address):
        postal_addr, postal_pcc = address.rsplit('\n', 1)
        return location_addr, location_pcc, postal_addr, postal_pcc

    if m := p5.match(address):
        postal_addr = m.group(1)
        if m.group(2):
            postal_addr += f'{m.group(2)}'
        return location_addr, location_pcc, postal_addr, postal_pcc

    # default no match found
    return location_addr, location_pcc, postal_addr, postal_pcc


@cli.command('migrate-people-address-field')
@click.option('--dry-run/--no-dry-run', default=False)
def migrate_people_address_field(
    dry_run: bool
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Migrates onegov_agency people address field.

    Migrate data from onegov_agency table 'people' column 'address' field to
    'location_address', 'location_code_city', 'postal_address' and
    'postal_code_city' fields.


    Example:

        onegov-people --select /onegov_agency/bs migrate-people-address-field

        onegov-people --select /onegov_agency/bs migrate-people-address-field
        --dry-run

    """

    def _migrate(request: 'CoreRequest', app: 'Framework') -> None:
        session = app.session()
        click.secho("Migrate data from table 'people' column 'address' "
                    "field to 'location_address', 'location_code_city', "
                    "'postal_address' and 'postal_code_city ..",
                    fg='yellow')
        migration_count = 0
        total_count = 0
        for person in session.query(Person):
            total_count += 1

            if not person.address:
                continue

            (
                person.location_address,
                person.location_code_city,
                person.postal_address,
                person.postal_code_city
            ) = parse_and_split_address_field(person.address)

            migration_count += 1

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

        click.secho(f'Migrated all {migration_count} address(es) of totally '
                    f'{total_count} people', fg='green')

    return _migrate


@cli.command('onegov-migrate-people-address-field')
@click.option('--dry-run/--no-dry-run', default=False)
def onegov_migrate_people_address_field(
    dry_run: bool
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Migrates people address field everywhere in onegov.

    Migrate data from 'people' column 'address' field to
    'location_address', 'location_code_city', 'postal_address' and
    'postal_code_city' fields.


    Example:

        onegov-people --select /onegov_town6/ebikon
        onegov-migrate-people-address-field

        onegov-people --select /onegov_org/risch
        onegov-migrate-people-address-field --dry-run

    """

    def _migrate(request: 'CoreRequest', app: 'Framework') -> None:
        click.secho(f'Request url: {request.url}..')
        session = app.session()
        click.secho("Onegov migrate data from table 'people' column "
                    "'address' field to 'location_address', "
                    "'location_code_city', 'postal_address' and "
                    "'postal_code_city ..",
                    fg='yellow')
        migration_count = 0
        total_count = 0
        for person in session.query(Person):
            total_count += 1

            if not person.address:
                continue

            (
                person.location_address,
                person.location_code_city,
                person.postal_address,
                person.postal_code_city
            ) = parse_and_split_address_field(person.address)

            migration_count += 1

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

        click.secho(f'Migrated all {migration_count} address(es) of totally '
                    f'{total_count} people', fg='green')

    return _migrate


re_postal_code_city_ch = re.compile(r'\d{4} .*')  # e.g. '1234 Mein Ort'
re_postal_code_city_de = re.compile(r'D-\d{5} .*')  # e.g. 'D-12345 Mein Ort'


def parse_agency_portrait_field_for_address(
    portrait: str
) -> tuple[str, str, str, str]:
    """
    Parsing the `portrait` field of agencies and extract address and
    code/city as well as location address and city if present.

    :param portrait: html str
    :return: tuple: (location_addr, location_pcc ,postal_address,
    postal_code_city)
    """

    location_addr = ''
    location_pcc = ''
    postal_addr = ''
    postal_pcc = ''
    plz_city_found_idx = -1

    soup = BeautifulSoup(portrait, "html.parser")
    # convert from html to text using soup
    portrait_text = soup.get_text('\n')
    lines = portrait_text.split('\n')
    for line, idx in zip(lines, range(len(lines))):
        if m := (re_postal_code_city_ch.match(line)
                 or re_postal_code_city_de.match(line)):

            if plz_city_found_idx:
                # assuming address initially found was location address
                location_addr = postal_addr
                location_pcc = postal_pcc

            postal_pcc = m.group(0)
            postal_addr = lines[idx - 1] if idx > 0 else ''  # if only
            # code/city no street and number

            # only extend postal address 'Postfach' with street/house number if
            # previous line is at least two lines away
            # Dorfstrasse 1, Postfach, 1234 Govikon
            if (
                'postfach' in postal_addr.lower()
                and (plz_city_found_idx + 2 < idx)
                and idx >= 2 and lines[idx - 2] != ''
            ):
                postal_addr = lines[idx - 2] + '\n' + postal_addr

            plz_city_found_idx = idx

    return location_addr, location_pcc, postal_addr, postal_pcc


@cli.command('extract-address-from-portrait-field')
@click.option('--dry-run/--no-dry-run', default=False)
def extract_address_from_portrait_field(
    dry_run: bool
) -> 'Callable[[CoreRequest, Framework], None]':
    """ Extracts address from onegov_agency agency portrait field.

    Extracts address, postal code and city from onegov_agency table
    'agencies' column 'portrait'.

    Example:

        onegov-people --select /onegov_agency/bs
         extract-address-from-portrait-field
        onegov-people --select /onegov_agency/bs
         extract-address-from-portrait-field --dry-run
    """

    def _extract(request: 'CoreRequest', app: 'Framework') -> None:
        session = app.session()
        click.secho("Extract address, postal code and city from table "
                    "'agencies' column 'portrait' to "
                    "'location_address', 'location_code_city', "
                    "'postal_address' and 'postal_code_city ..",
                    fg='yellow')
        extraction_count = 0
        total_count = 0
        for agency in session.query(Agency):
            total_count += 1

            if not agency.portrait:
                continue

            (
                agency.location_address,
                agency.location_code_city,
                agency.postal_address,
                agency.postal_code_city
            ) = parse_agency_portrait_field_for_address(agency.portrait)

            extraction_count += 1

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

        transaction.commit()
        click.secho(f'Extracted {extraction_count} address(es) of totally '
                    f'{total_count} agencies', fg='green')

    return _extract
