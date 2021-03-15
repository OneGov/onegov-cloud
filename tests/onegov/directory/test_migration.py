from tempfile import NamedTemporaryFile

from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.directory.migration import StructuralChanges
from tests.shared.utils import create_image


def test_detect_added_fields():
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


def test_detect_removed_fields():
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


def test_detect_renamed_fields():
    changes = StructuralChanges(
        """
            First Name = ___
        """,
        """
            Name = ___
        """
    )

    assert changes.renamed_fields == {'First Name': 'Name'}

    changes = StructuralChanges(
        """
            # General
            First Name = ___
        """,
        """
            # Personal
            Name = ___
        """
    )

    assert changes.renamed_fields == {'General/First Name': 'Personal/Name'}

    changes = StructuralChanges(
        """
            # General
            First Name = ___
        """,
        """
            # Personal
            Name = ___
        """
    )

    assert changes.renamed_fields == {'General/First Name': 'Personal/Name'}

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


def test_detect_changed_fields():
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


def test_remove_fieldset_in_between():
    changes = StructuralChanges(
        """ # F
            A = ___
            # S
            B = ___
            # T
            C = ___
        """,
        """ # F
            A = ___
            B = ___
            # T
            C = ___
        """
    )
    assert not changes.added_fields
    assert not changes.removed_fields
    assert changes.renamed_fields == {'S/B': 'F/B'}
    assert not changes.changed_fields


def test_directory_migration(session):
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
        cost_currency='EUR'
    ))

    print([f.id for f in zoos.basic_fields])

    new_structure = """
        # Main
        Name *= ___
        Logo = *.png
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

    migration = zoos.migration(
        new_structure, zoos.configuration
    )
    changes = migration.changes
    assert changes.renamed_fields == {
        'General/Employees': 'Main/Employees',
        'General/Epoch': 'Main/Epoch',
        'General/Landscapes': 'Main/Landscape'
    }
    assert changes.changed_fields == []
    assert migration.possible
