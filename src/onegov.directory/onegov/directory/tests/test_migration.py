from onegov.directory.migration import StructuralChanges


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
