from __future__ import annotations

from onegov.directory.models.directory_entry import DirectoryEntry
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import parse_form
from onegov.form import parse_formcode
from onegov.form.parser.core import OptionsField
from sqlalchemy.orm import object_session, joinedload, undefer
from sqlalchemy.orm.attributes import get_history
from wtforms import ValidationError

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from datetime import date, datetime, time
    from onegov.directory.models import Directory
    from onegov.directory.types import DirectoryConfiguration


class DirectoryMigration:
    """ Takes a directory and the structure/configuration it should have in
    the future.

    It then migrates the existing directory entries, if possible.

    """

    def __init__(
        self,
        directory: Directory,
        new_structure: str | None = None,
        new_configuration: DirectoryConfiguration | None = None,
        old_structure: str | None = None
    ):

        self.directory = directory
        self.old_structure = old_structure or self.old_directory_structure

        self.new_structure = new_structure or directory.structure
        self.new_configuration = new_configuration or directory.configuration

        self.new_form_class = parse_form(self.new_structure)
        self.fieldtype_migrations = FieldTypeMigrations()

        self.changes = StructuralChanges(
            self.old_structure,
            self.new_structure
        )

    @property
    def old_directory_structure(self) -> str:
        history = get_history(self.directory, 'structure')

        if history.deleted:
            return history.deleted[0]
        else:
            return self.directory.structure

    @property
    def possible(self) -> bool:
        """ Returns True if the migration is possible, False otherwise. """
        if not self.directory.entries:
            return True

        if not self.changes:
            return True

        if len(self.changes.renamed_options) > 1:
            return False

        if self.multiple_option_changes_in_one_step():
            return False

        if self.added_required_fields():
            return False

        for changed in self.changes.changed_fields:
            old = self.changes.old[changed]
            new = self.changes.new[changed]

            # we can turn required into optional fields and vice versa
            # (the form validation takes care of validating the requirements)
            if old.required != new.required and old.type == new.type:
                continue

            # we can only convert certain types
            if old.required == new.required and old.type != new.type:
                if not self.fieldtype_migrations.possible(old.type, new.type):
                    break
        else:
            return True

        return False

    @property
    def entries(self) -> Iterable[DirectoryEntry]:
        session = object_session(self.directory)

        if not session:
            return self.directory.entries

        e = session.query(DirectoryEntry)
        e = e.filter_by(directory_id=self.directory.id)
        e = e.options(joinedload(DirectoryEntry.files))
        e = e.options(undefer(DirectoryEntry.content))

        return e

    def execute(self) -> None:
        """ To run the migration, run this method. The other methods below
        should only be used if you know what you are doing.

        """
        if self.added_required_fields():
            raise ValidationError(
                '${fields}: New fields cannot be required initially. '
                  'Require them in a separate migration step.'.format(
                    fields=', '.join(
                        f'"{f}"' for f in self.get_added_required_field_ids())
                )
            )

        assert self.possible

        self.migrate_directory()

        # Triggers the observer to func::structure_configuration_observer()
        # and executing this very function because of an autoflush event
        # in a new instance.
        for entry in self.entries:
            self.migrate_entry(entry)

    def migrate_directory(self) -> None:
        self.directory.structure = self.new_structure
        self.directory.configuration = self.new_configuration

    def migrate_entry(self, entry: DirectoryEntry) -> None:
        """
        This function is called after an update to the directory structure.
        During execution of self.execute(), the directory is migrated.
        On start of looping trough the entries, an auto_flush occurs, calling
        the migration observer for the directory, which will instantiate yet
        another instance of the migration. After this inside execute(),
        the session is not flusing anymore, and we have to skip,
        since the values are already migrated and migration will
        fail when removing fieldsets.
        """
        update = self.changes and True or False
        session = object_session(entry)
        assert session is not None

        if not session._flushing:
            return
        self.migrate_values(entry.values)
        self.directory.update(entry, entry.values, force_update=update)

    def migrate_values(self, values: dict[str, Any]) -> None:
        self.add_new_fields(values)
        self.remove_old_fields(values)
        self.rename_fields(values)
        self.convert_fields(values)
        self.rename_options(values)
        self.remove_old_options(values)

    def add_new_fields(self, values: dict[str, Any]) -> None:
        for added in self.changes.added_fields:
            added = as_internal_id(added)
            values[added] = None

    def remove_old_fields(self, values: dict[str, Any]) -> None:
        for removed in self.changes.removed_fields:
            removed = as_internal_id(removed)
            del values[removed]

    def rename_fields(self, values: dict[str, Any]) -> None:
        for old, new in self.changes.renamed_fields.items():
            old, new = as_internal_id(old), as_internal_id(new)
            values[new] = values[old]
            del values[old]

    def convert_fields(self, values: dict[str, Any]) -> None:
        for changed in self.changes.changed_fields:
            convert = self.fieldtype_migrations.get_converter(
                self.changes.old[changed].type,
                self.changes.new[changed].type
            )
            assert convert is not None

            changed = as_internal_id(changed)
            values[changed] = convert(values[changed])

    def rename_options(self, values: dict[str, Any]) -> None:
        for old_option, new_option in self.changes.renamed_options.items():
            old_label = old_option[1]
            new_label = new_option[1]
            for key, val in list(values.items()):
                if isinstance(val, list):
                    values[key] = [
                        new_label if v == old_label else v for v in val
                    ]

                elif val == old_label:
                    values[key] = new_label

    def remove_old_options(self, values: dict[str, Any]) -> None:
        for human_id, label in self.changes.removed_options:
            id = as_internal_id(human_id)
            if id in values:
                if isinstance(values[id], list):
                    values[id] = [v for v in values[id] if v != label]
                elif values[id] == label:
                    values[id] = None

    def multiple_option_changes_in_one_step(self) -> bool:
        """
        Returns True if there are multiple changes e.g. added and
        removed options.
        """

        if (
            (self.changes.added_options and self.changes.removed_options)
            or (self.changes.added_options and self.changes.renamed_options)
            or (self.changes.removed_options and self.changes.renamed_options)
        ):
            return True
        return False

    def added_required_fields(self) -> bool:
        """
        Identify newly added fields that are set to be required. Newly added
        fields shall not be required if entries exist, make them required
        in a separate migration step.
        """
        if self.directory.entries:
            return any(
                f.required for f in self.changes.new.values()
                if f.human_id in self.changes.added_fields
            )

        return False

    def get_added_required_field_ids(self) -> list[str]:
        return [
            f.human_id for f in self.changes.new.values()
            if f.required and f.human_id in self.changes.added_fields
        ]


class FieldTypeMigrations:
    """ Contains methods to migrate fields from one type to another. """

    def possible(self, old_type: str, new_type: str) -> bool:
        return self.get_converter(old_type, new_type) is not None

    def get_converter(
        self,
        old_type: str,
        new_type: str
    ) -> Callable[[Any], Any] | None:

        if old_type == 'password':
            return None  # disabled to avoid accidental leaks

        if old_type == new_type:
            return lambda v: v

        explicit = f'{old_type}_to_{new_type}'
        generic = f'any_to_{new_type}'

        return getattr(self, explicit, getattr(self, generic, None))

    def any_to_text(self, value: Any) -> str:
        return str(value if value is not None else '').strip()

    def any_to_textarea(self, value: Any) -> str:
        return self.any_to_text(value)

    def textarea_to_text(self, value: str) -> str:
        return value.replace('\n', ' ').strip()

    def textarea_to_code(self, value: str) -> str:
        return value

    def text_to_code(self, value: str) -> str:
        return value

    def date_to_text(self, value: date) -> str:
        return '{:%d.%m.%Y}'.format(value) if value else ''

    def datetime_to_text(self, value: datetime) -> str:
        return '{:%d.%m.%Y %H:%M}'.format(value) if value else ''

    def time_to_text(self, value: time) -> str:
        return '{:%H:%M}'.format(value) if value else ''

    def radio_to_checkbox(self, value: str) -> list[str]:
        return [value] if value else []

    def text_to_url(self, value: str) -> str:
        return value


class StructuralChanges:
    """ Tries to detect structural changes between two formcode blocks.

    Can only be trusted if the ``detection_successful`` property is True. If it
    is not, the detection failed because the changes were too great.

    """

    def __init__(self, old_structure: str, new_structure: str) -> None:
        old_fieldsets = parse_formcode(old_structure)
        new_fieldsets = parse_formcode(new_structure)
        self.old = {
            f.human_id: f for f in flatten_fieldsets(old_fieldsets)
        }
        self.new = {
            f.human_id: f for f in flatten_fieldsets(new_fieldsets)
        }
        self.old_fieldsets = old_fieldsets
        self.new_fieldsets = new_fieldsets

        self.detect_added_fieldsets()
        self.detect_removed_fieldsets()
        self.detect_added_fields()
        self.detect_removed_fields()
        self.detect_renamed_fields()  # modifies added/removed fields
        self.detect_changed_fields()
        self.detect_added_options()
        self.detect_removed_options()
        self.detect_renamed_options()

    def __bool__(self) -> bool:
        return bool(
            self.added_fields
            or self.removed_fields
            or self.renamed_fields
            or self.changed_fields
            or self.added_options
            or self.removed_options
            or self.renamed_options  # radio and checkboxes
        )

    def detect_removed_fieldsets(self) -> None:
        new_ids = tuple(f.human_id for f in self.new_fieldsets if f.human_id)
        self.removed_fieldsets = [
            f.human_id for f in self.old_fieldsets
            if f.human_id and f.human_id not in new_ids
        ]

    def detect_added_fieldsets(self) -> None:
        old_ids = tuple(f.human_id for f in self.old_fieldsets if f.human_id)
        self.added_fieldsets = [
            f.human_id for f in self.new_fieldsets
            if f.human_id and f.human_id not in old_ids
        ]

    def detect_added_fields(self) -> None:
        self.added_fields = [
            f.human_id for f in self.new.values()
            if f.human_id not in {f.human_id for f in self.old.values()}
        ]

    def detect_removed_fields(self) -> None:
        self.removed_fields = [
            f.human_id for f in self.old.values()
            if f.human_id not in {f.human_id for f in self.new.values()}
        ]

    def do_rename(self, removed: str, added: str) -> bool:
        if removed in self.renamed_fields:
            return False
        if added in set(self.renamed_fields.values()):
            return False
        same_type = self.old[removed].type == self.new[added].type
        if not same_type:
            return False

        added_fs = '/'.join(added.split('/')[:-1])
        removed_fs = '/'.join(removed.split('/')[:-1])

        # has no fieldset
        if not added_fs and not removed_fs:
            return same_type

        # case fieldset/Oldname --> Oldname
        if removed_fs and not added_fs:
            if f'{removed_fs}/{added}' == removed:
                return True

        # case Oldname --> fieldset/Name
        if added_fs and not removed_fs:
            if f'{added_fs}/{removed}' == added:
                return True

        # case fieldset rename and field rename

        in_removed = any(s == removed_fs for s in self.removed_fieldsets)
        in_added = any(s == added_fs for s in self.added_fieldsets)

        # Fieldset rename
        expected = f'{added_fs}/{removed.split("/")[-1]}'
        if in_added and in_removed:
            if expected == added:
                return True
            if expected in self.added_fields:
                return False
            if added not in self.renamed_fields.values():
                # Prevent assigning same new field twice
                return True

        # Fieldset has been deleted
        if (in_removed and not in_added) or (in_added and not in_removed):
            if expected == added:
                # It matches exactly
                return True
            if expected in self.added_fields:
                # there is another field that matches better
                return False
        # if len(self.added_fields) == len(self.removed_fields) == 1:
        #     return True
        return True

    def detect_renamed_fields(self) -> None:
        # renames are detected aggressively - we rather have an incorrect
        # rename than an add/remove combo. Renames lead to no data loss, while
        # a add/remove combo does.
        self.renamed_fields = {}

        for r in self.removed_fields:
            for a in self.added_fields:
                if self.do_rename(r, a):
                    self.renamed_fields[r] = a

        self.added_fields = [
            f for f in self.added_fields
            if f not in set(self.renamed_fields.values())
        ]
        self.removed_fields = [
            f for f in self.removed_fields
            if f not in self.renamed_fields
        ]

    def detect_changed_fields(self) -> None:
        self.changed_fields = []

        for old_id, old in self.old.items():
            if old_id in self.renamed_fields:
                new_id = self.renamed_fields[old_id]
            elif old_id in self.new:
                new_id = old_id
            else:
                continue

            new = self.new[new_id]
            if old.required != new.required or old.type != new.type:
                self.changed_fields.append(new_id)

    def detect_added_options(self) -> None:
        self.added_options = []

        for old_id, old_field in self.old.items():
            if isinstance(old_field, OptionsField) and old_id in self.new:
                new_field = self.new[old_id]
                if isinstance(new_field, OptionsField):
                    new_labels = [r.label for r in new_field.choices]
                    old_labels = [r.label for r in old_field.choices]

                    for n in new_labels:
                        if n not in old_labels:
                            self.added_options.append((old_id, n))

    def detect_removed_options(self) -> None:
        self.removed_options = []

        for old_id, old_field in self.old.items():
            if isinstance(old_field, OptionsField) and old_id in self.new:
                new_field = self.new[old_id]
                if isinstance(new_field, OptionsField):
                    new_labels = [r.label for r in new_field.choices]
                    old_labels = [r.label for r in old_field.choices]

                    for o in old_labels:
                        if o not in new_labels:
                            self.removed_options.append((old_id, o))

    def detect_renamed_options(self) -> None:
        self.renamed_options = {}

        for old_id, old_field in self.old.items():
            if isinstance(old_field, OptionsField) and old_id in self.new:
                new_field = self.new[old_id]
                if isinstance(new_field, OptionsField):
                    old_labels = [r.label for r in old_field.choices]
                    new_labels = [r.label for r in new_field.choices]

                    if old_labels == new_labels:
                        continue

                    # test if re-ordered
                    if set(old_labels) == set(new_labels):
                        continue

                    # only consider renames if the number of options
                    # remains the same
                    if len(old_labels) != len(new_labels):
                        continue

                    for o_label, n_label in zip(old_labels, new_labels):
                        if o_label != n_label:
                            self.renamed_options[(old_id, o_label)] = (
                                old_id,
                                n_label
                            )

                        self.added_options = [
                            ao for ao in self.added_options
                            if ao not in self.renamed_options.values()
                        ]
                        self.removed_options = [
                            ro for ro in self.removed_options
                            if ro not in self.renamed_options.keys()
                        ]
