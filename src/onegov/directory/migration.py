from __future__ import annotations

from onegov.directory.models.directory_entry import DirectoryEntry
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import parse_form
from onegov.form import parse_formcode
from sqlalchemy.orm import object_session, joinedload, undefer
from sqlalchemy.orm.attributes import get_history


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
        if not self.directory.entries:
            return True

        if not self.changes:
            return True

        if not self.changes.changed_fields:
            return True

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

        if not session._flushing:
            return
        self.migrate_values(entry.values)
        self.directory.update(entry, entry.values, force_update=update)

    def migrate_values(self, values: dict[str, Any]) -> None:
        self.add_new_fields(values)
        self.remove_old_fields(values)
        self.rename_fields(values)
        self.convert_fields(values)

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

    # FIXME: A lot of these converters currently don't work if the value
    #        happens to be None, which should be possible for every field
    #        as long as its optional, or do we skip converting None
    #        explicitly somewhere?!
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
        return '{:%d.%m.%Y}'.format(value)

    def datetime_to_text(self, value: datetime) -> str:
        return '{:%d.%m.%Y %H:%M}'.format(value)

    def time_to_text(self, value: time) -> str:
        return '{:%H:%M}'.format(value)

    def radio_to_checkbox(self, value: str) -> list[str]:
        return [value]

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

    def __bool__(self) -> bool:
        return bool(
            self.added_fields
            or self.removed_fields
            or self.renamed_fields
            or self.changed_fields
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
