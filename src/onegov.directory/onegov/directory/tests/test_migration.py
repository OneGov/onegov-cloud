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

    assert changes.added_fields == ['last_name']


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

    assert changes.removed_fields == ['last_name']


def test_detect_renamed_fields():
    changes = StructuralChanges(
        """
            First Name = ___
        """,
        """
            Name = ___
        """
    )

    assert changes.renamed_fields == {'first_name': 'name'}

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

    assert changes.renamed_fields == {'general_first_name': 'personal_name'}

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

    assert changes.renamed_fields == {'general_first_name': 'personal_name'}

    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Comment = ...
        """
    )

    assert changes.removed_fields == ['name']
    assert changes.added_fields == ['comment']


def test_detect_changed_fields():
    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Name *= ___
        """
    )

    assert changes.changed_fields == ['name']

    changes = StructuralChanges(
        """
            First Name = ___
        """,
        """
            Name *= ___
        """
    )

    assert changes.renamed_fields == {'first_name': 'name'}
    assert changes.changed_fields == ['name']

    changes = StructuralChanges(
        """
            Name = ___
        """,
        """
            Name = ...
        """
    )

    assert changes.changed_fields == ['name']
