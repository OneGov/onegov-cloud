from __future__ import annotations

from click.testing import CliRunner
from onegov.people.cli import cli
from onegov.people.models import Person
from pathlib import Path
from transaction import commit


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


def test_cli(
    cfg_path: str,
    session_manager: SessionManager,
    temporary_directory: str
) -> None:

    runner = CliRunner()

    # Clear
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'clear'
    ], input='y\n')
    assert result.exit_code == 0
    assert 'Deleted 0 person(s)' in result.output

    # Empty export
    filename = Path(temporary_directory) / 'empty.xlsx'
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'export', str(filename)
    ])
    assert result.exit_code == 0
    assert 'Exported 0 person(s)' in result.output

    # Add some people
    session = session_manager.session()
    session.add(
        Person(
            salutation='Mr.',
            academic_title='Dr.',
            first_name='Hans',
            last_name='Moleman',
            function='King of the Mole People',
            email='hans.moleman@foo.bar',
            phone='+123456',
            phone_direct='+456789',
            born='1.1.1910',
            profession='Former Major',
            political_party='Republican Party',
            parliamentary_group='Republicans',
            organisation='Super Org',
            sub_organisation='Sub Org',
            website='https://foo.bar',
            postal_address='Fakestreet 123',
            postal_code_city='1234 Govikon',
            picture_url='https://foo.bar/hans-molman/portrait.png',
            notes='Almost entirely blind',
        )
    )
    session.add(
        Person(
            first_name='Edna',
            last_name='Krabappel',
            function='Teacher',
            email='edna.krabappel@foo.bar',
            profession='Teacher',
        )
    )
    session.flush()
    commit()

    # Export
    filename = Path(temporary_directory) / 'people.xlsx'
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'export', str(filename)
    ])
    assert result.exit_code == 0
    assert 'Exported 2 person(s)' in result.output

    # Clear
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'clear'
    ], input='y\n')
    assert result.exit_code == 0
    assert 'Deleted 2 person(s)' in result.output
    assert session.query(Person).count() == 0

    # Import
    filename = Path(temporary_directory) / 'people.xlsx'
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import', str(filename)
    ])
    assert result.exit_code == 0
    assert 'Imported 2 person(s)' in result.output
    assert session.query(Person).count() == 2

    person = session.query(Person).filter_by(first_name='Hans').one()
    assert person.salutation == 'Mr.'
    assert person.academic_title == 'Dr.'
    assert person.first_name == 'Hans'
    assert person.last_name == 'Moleman'
    assert person.function == 'King of the Mole People'
    assert person.email == 'hans.moleman@foo.bar'
    assert person.phone == '+123456'
    assert person.phone_direct == '+456789'
    assert person.born == '1.1.1910'
    assert person.profession == 'Former Major'
    assert person.political_party == 'Republican Party'
    assert person.parliamentary_group == 'Republicans'
    assert person.organisation == 'Super Org'
    assert person.sub_organisation == 'Sub Org'
    assert person.website == 'https://foo.bar'
    assert person.postal_address == 'Fakestreet 123'
    assert person.postal_code_city == '1234 Govikon'
    assert person.picture_url == 'https://foo.bar/hans-molman/portrait.png'
    assert person.notes == 'Almost entirely blind'

    person = session.query(Person).filter_by(first_name='Edna').one()
    assert person.salutation is None
    assert person.academic_title is None
    assert person.first_name == 'Edna'
    assert person.last_name == 'Krabappel'
    assert person.function == 'Teacher'
    assert person.email == 'edna.krabappel@foo.bar'
    assert person.phone is None
    assert person.phone_direct is None
    assert person.born is None
    assert person.profession == 'Teacher'
    assert person.political_party is None
    assert person.parliamentary_group is None
    assert person.organisation is None
    assert person.sub_organisation is None
    assert person.website is None
    assert person.postal_address is None
    assert person.picture_url is None
    assert person.notes is None

    # Import (empty)
    filename = Path(temporary_directory) / 'empty.xlsx'
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/foo/bar',
        'import', str(filename)
    ])
    assert result.exit_code == 0
    assert 'Imported 0 person(s)' in result.output
