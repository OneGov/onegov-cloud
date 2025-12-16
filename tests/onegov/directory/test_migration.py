from __future__ import annotations

import pytest
import textwrap

from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.directory.migration import StructuralChanges
from onegov.form.errors import DuplicateLabelError
from tempfile import NamedTemporaryFile
from tests.shared.utils import create_image

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_detect_added_fields() -> None:
    changes = StructuralChanges(
        """
            First Name = ___
        """,
        """
            First Name = ___
            Last Name = ___
        """
    )

    assert changes.added_fields == ['Last Name']
    assert not changes.removed_fields
    assert not changes.renamed_fields
    assert not changes.added_fieldsets
    assert not changes.removed_fieldsets


def test_detect_removed_fields() -> None:
    changes = StructuralChanges(
        """
            First Name = ___
            Last Name = ___
        """,
        """
            First Name = ___
        """
    )

    assert changes.removed_fields == ['Last Name']
    assert not changes.renamed_fields
    assert not changes.added_fields
    assert not changes.added_fieldsets
    assert not changes.removed_fieldsets


def test_duplicate_label_error() -> None:

    with pytest.raises(DuplicateLabelError):
        StructuralChanges(
            'A *= ___',
            'A *= ___\nA *= ___',
        )


def test_detect_renamed_fields() -> None:
    changes = StructuralChanges(
        """
            # F
            Other = ___
            Name = ___
            Bottom = ___
        """,
        """
            # F
            Other New = ___
            Name = ___
            Bottom New = ___
        """
    )

    assert changes.renamed_fields == {
        'F/Other': 'F/Other New', 'F/Bottom': 'F/Bottom New'}

    changes = StructuralChanges(
        """
            # F
            Name = ___
            Bottom = ___
        """,
        """
            # F
            Name New = ___
            Bottom = ___
        """
    )

    assert changes.renamed_fields == {'F/Name': 'F/Name New'}

    changes = StructuralChanges(
        """
            Top = ___
            First Name = ___
            Bottom = ___
        """,
        """
            Top = ___
            Name = ___
            Bottom = ___
        """
    )

    assert changes.renamed_fields == {'First Name': 'Name'}

    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Comment = ...
        """
    )

    assert changes.removed_fields == ['Name']
    assert changes.added_fields == ['Comment']


def test_detect_renamed_fields_changing_fieldsets() -> None:
    changes = StructuralChanges(
        """
            # General
            First Name = ___
            Other = ___
        """,
        """
            # Personal
            Name = ___
            Other = ___
        """
    )
    assert changes.renamed_fields == {
        'General/First Name': 'Personal/Name',
        'General/Other': 'Personal/Other'
    }
    assert not changes.removed_fields
    assert not changes.added_fields
    assert changes.removed_fieldsets == ['General']
    assert changes.added_fieldsets == ['Personal']

    # there is a limit of what can be done...
    # but it should since the order persisted and a new field is only
    # assigned once
    old = """
    # General
    First Name = ___
    Other = ___
    Third = ___
    """
    new = """
    # Personal
    Name = ___
    Other too = ___
    Third Renamed = ___
    """
    changes = StructuralChanges(old, new)
    assert changes.renamed_fields == {
        'General/First Name': 'Personal/Name',
        'General/Other': 'Personal/Other too',
        'General/Third': 'Personal/Third Renamed'
    }

    # Testing the same with an additional type change without renaming the
    # field itself
    changes = StructuralChanges(
        old,
        new.replace('Other too = ___', 'Other = ...')
    )
    assert changes.renamed_fields == {
        'General/First Name': 'Personal/Name',
        'General/Third': 'Personal/Third Renamed'
    }
    assert changes.added_fields == ['Personal/Other']
    assert changes.removed_fields == ['General/Other']


def test_detect_changed_fields() -> None:
    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Name *= ___
        """
    )

    assert changes.changed_fields == ['Name']

    changes = StructuralChanges(
        """
            First Name = ___
        """,
        """
            Name *= ___
        """
    )

    assert changes.renamed_fields == {'First Name': 'Name'}
    assert changes.changed_fields == ['Name']

    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Name = ...
        """
    )

    assert changes.changed_fields == ['Name']


def test_add_fieldset_at_top() -> None:
    old = textwrap.dedent("""
    A *= ___
    # Unchanged
    B *= ___
    C *= ___""")

    changes = StructuralChanges(old, '# Main\n' + old)
    assert not changes.removed_fieldsets
    assert changes.added_fieldsets == ['Main']
    assert changes.renamed_fields == {'A': 'Main/A'}
    assert not changes.added_fields
    assert not changes.removed_fields


def test_add_fieldset_at_bottom() -> None:
    old = textwrap.dedent("""
    A *= ___
    B *= ___
    C *= ___""")

    new = textwrap.dedent("""
    A *= ___
    B *= ___
    # Crazy
    C *= ___""")

    changes = StructuralChanges('# Main\n' + old, '# Main\n' + new)
    assert not changes.removed_fieldsets
    assert changes.added_fieldsets == ['Crazy']
    assert changes.renamed_fields == {'Main/C': 'Crazy/C'}
    assert not changes.added_fields
    assert not changes.removed_fields

    changes = StructuralChanges(old, new)
    assert not changes.removed_fieldsets
    assert changes.added_fieldsets == ['Crazy']
    assert changes.renamed_fields == {'C': 'Crazy/C'}
    assert not changes.added_fields
    assert not changes.removed_fields


def test_remove_fieldset_in_between() -> None:

    old = """
        # Main
        Name *= ___
        # Cost (A,B;C/D)
        Cost *= ___
        << z.B. (/) >>
        Currency *= ___"""

    # Test topmost fieldset deleted with fieldsets beneath
    changes = StructuralChanges(old, old.replace('# Main', ''))
    assert not changes.added_fieldsets
    assert changes.renamed_fields == {'Main/Name': 'Name'}
    assert not changes.added_fields
    assert not changes.removed_fields
    assert changes.removed_fieldsets == ['Main']

    changes = StructuralChanges(old, old.replace('# Cost (A,B;C/D)', ''))
    assert changes.renamed_fields == {
        'Cost (A,B;C/D)/Cost': 'Main/Cost',
        'Cost (A,B;C/D)/Currency': 'Main/Currency'
    }
    assert not changes.added_fieldsets
    assert not changes.added_fields
    assert not changes.removed_fields
    assert not changes.added_fieldsets
    assert changes.removed_fieldsets == ['Cost (A,B;C/D)']

    old = """
    # F
    A = ___
    # S
    B = ___
    C = ___
    # T
    D = ___"""

    changes = StructuralChanges(
        old,
        old.replace('# S', '')
    )
    assert changes.renamed_fields == {'S/B': 'F/B', 'S/C': 'F/C'}
    assert not changes.added_fieldsets
    assert changes.removed_fieldsets == ['S']
    assert not changes.removed_fields
    assert not changes.added_fields
    assert not changes.changed_fields


def test_directory_migration(session: Session) -> None:
    """
    Testcases:
    - nested radio fields
    - nested checkbox fields
    - file fields
    - changing fieldset titles
    - removing a fieldset in between two other fieldsets
    """
    directories = DirectoryCollection(session)
    structure = """
        # Main
        Name *= ___
        Logo = *.png
        # General
        Employees = 0..1000
        << All sorts are counted >>
        Epoch *=
            ( ) Before 1950
            ( ) After 1950
        Landscapes =
            [ ] Tundra
            [ ] Arctic
            [ ] Desert
        # Cost (A,B;C/D)
        Cost *= ___
        << z.B. (/) >>
        Currency *= ___
       """
    zoos = directories.add(
        title="Zoos",
        lead="The town's zoos",
        structure=structure,
        configuration=DirectoryConfiguration(
            title="[Main/Name]",
            order=['Main/Name']
        )
    )
    output = NamedTemporaryFile(suffix='.png')
    zoos.add(values=dict(
        main_name="Berliner Zoo",
        general_employees=450,
        main_logo=Bunch(
            data=object(),
            file=create_image(output=output).file,
            filename='logo.png'
        ),
        general_epoch='Before 1950',
        general_landscapes=['Tundra'],
        cost_a_b_c_d_cost=15,
        cost_a_b_c_d_currency='EUR'
    ))

    # Remove fieldset in between without having to change configuration
    new_structure = structure.replace('# General', '')
    migration = zoos.migration(new_structure, new_configuration=None)
    changes = migration.changes
    assert changes.renamed_fields == {
        'General/Employees': 'Main/Employees',
        'General/Epoch': 'Main/Epoch',
        'General/Landscapes': 'Main/Landscapes'
    }
    assert not changes.changed_fields
    assert migration.possible

    # First migrates directory, then updates each entry.
    migration.execute()

    new_structure = new_structure.replace('# Cost (A,B;C/D)', '')
    migration = zoos.migration(new_structure, None)
    changes = migration.changes
    assert changes.renamed_fields['Cost (A,B;C/D)/Currency'] == 'Main/Currency'
    assert changes.renamed_fields['Cost (A,B;C/D)/Cost'] == 'Main/Cost'
    assert not changes.changed_fields
    assert migration.possible

    migration.execute()


def test_directory_fieldtype_migrations(session: Session) -> None:
    """
    The issue with migrations is that if one directory entry does not specify
    a value for a field the migration ends up in a `ValidationError`
    """

    structure = """
        # Main
        Name *= ___
        # General
        Landscapes =
            ( ) Tundra
            ( ) Arctic
            ( ) Desert
    """

    new_structure = """
        # Main
        Name *= ___
        # General
        Landscapes =
            [ ] Tundra
            [ ] Arctic
            [ ] Desert
    """

    directories = DirectoryCollection(session)
    zoos = directories.add(
        title="Zoos",
        lead="The town's zoos",
        structure=structure,
        configuration=DirectoryConfiguration(
            title="[Main/Name]",
            order=['Main/Name']
        )
    )
    zoo = zoos.add(values=dict(
        main_name="Luzerner Zoo",
        general_landscapes='',  # No value is set
    ))

    assert zoo.values['general_landscapes'] == ''  # radio

    migration = zoos.migration(new_structure, None)
    changes = migration.changes
    assert migration.fieldtype_migrations.possible('radio', 'checkbox')

    migration.execute()

    assert zoo.values['general_landscapes'] == []  # checkbox
