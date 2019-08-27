from onegov.directory.models.directory_entry import DirectoryEntry
from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import parse_form
from onegov.form import parse_formcode
from sqlalchemy.orm import object_session, joinedload, undefer
from sqlalchemy.orm.attributes import get_history


class DirectoryMigration(object):
    """ Takes a directory and the structure/configuration it should have in
    the future.

    It then migrates the existing directory entries, if possible.

    """

    def __init__(self, directory, new_structure=None, new_configuration=None,
                 old_structure=None):

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
    def old_directory_structure(self):
        history = get_history(self.directory, 'structure')

        if history.deleted:
            return history.deleted[0]
        else:
            return self.directory.structure

    @property
    def possible(self):
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
    def entries(self):
        session = object_session(self.directory)

        if not session:
            return self.directory.entries

        e = session.query(DirectoryEntry)
        e = e.filter_by(directory_id=self.directory.id)
        e = e.options(joinedload(DirectoryEntry.files))
        e = e.options(undefer(DirectoryEntry.content))

        return e

    def execute(self):
        """ To run the migration, run this method. The other methods below
        should only be used if you know what you are doing.

        """
        assert self.possible

        self.migrate_directory()

        for entry in self.entries:
            self.migrate_entry(entry)

    def migrate_directory(self):
        self.directory.structure = self.new_structure
        self.directory.configuration = self.new_configuration

    def migrate_entry(self, entry):
        update = self.changes and True or False

        self.migrate_values(entry.values)
        self.directory.update(entry, entry.values, force_update=update)

    def migrate_values(self, values):
        self.add_new_fields(values)
        self.remove_old_fields(values)
        self.rename_fields(values)
        self.convert_fields(values)

    def add_new_fields(self, values):
        for added in self.changes.added_fields:
            added = as_internal_id(added)
            values[added] = None

    def remove_old_fields(self, values):
        for removed in self.changes.removed_fields:
            removed = as_internal_id(removed)
            del values[removed]

    def rename_fields(self, values):
        for old, new in self.changes.renamed_fields.items():
            old, new = as_internal_id(old), as_internal_id(new)
            values[new] = values[old]
            del values[old]

    def convert_fields(self, values):
        for changed in self.changes.changed_fields:
            convert = self.fieldtype_migrations.get_converter(
                self.changes.old[changed].type,
                self.changes.new[changed].type
            )

            changed = as_internal_id(changed)
            values[changed] = convert(values[changed])


class FieldTypeMigrations(object):
    """ Contains methods to migrate fields from one type to another. """

    def possible(self, old_type, new_type):
        return self.get_converter(old_type, new_type) is not None

    def get_converter(self, old_type, new_type):

        if old_type == 'password':
            return  # disabled to avoid accidental leaks

        if old_type == new_type:
            return lambda v: v

        explicit = '{}_to_{}'.format(old_type, new_type)
        generic = 'any_to_{}'.format(new_type)

        if hasattr(self, explicit):
            return getattr(self, explicit)

        if hasattr(self, generic):
            return getattr(self, generic)

    def any_to_text(self, value):
        return str(value if value is not None else '').strip()

    def any_to_textarea(self, value):
        return self.any_to_text(value)

    def textarea_to_text(self, value):
        return value.replace('\n', ' ').strip()

    def textarea_to_code(self, value):
        return value

    def text_to_code(self, value):
        return value

    def date_to_text(self, value):
        return '{:%d.%m.%Y}'.format(value)

    def datetime_to_text(self, value):
        return '{:%d.%m.%Y %H:%M}'.format(value)

    def time_to_text(self, value):
        return '{:%H:%M}'.format(value)

    def radio_to_checkbox(self, value):
        return value

    def text_to_url(self, value):
        return value


class StructuralChanges(object):
    """ Tries to detect structural changes between two formcode blocks.

    Can only be trusted if the ``detection_successful`` property is True. If it
    is not, the detection failed because the changes were too great.

    """

    def __init__(self, old_structure, new_structure):
        self.old = {
            f.human_id: f for f in flatten_fieldsets(
                parse_formcode(old_structure))
        }
        self.new = {
            f.human_id: f for f in flatten_fieldsets(
                parse_formcode(new_structure))
        }

        self.detect_added_fields()
        self.detect_removed_fields()
        self.detect_renamed_fields()  # modifies added/removed fields
        self.detect_changed_fields()

    def __bool__(self):
        return bool(
            self.added_fields
            or self.removed_fields
            or self.renamed_fields
            or self.changed_fields
        )

    def detect_added_fields(self):
        self.added_fields = [
            f.human_id for f in self.new.values()
            if f.human_id not in {f.human_id for f in self.old.values()}
        ]

    def detect_removed_fields(self):
        self.removed_fields = [
            f.human_id for f in self.old.values()
            if f.human_id not in {f.human_id for f in self.new.values()}
        ]

    def detect_renamed_fields(self):
        # renames are detected aggressively - we rather have an incorrect
        # rename than an add/remove combo. Renames lead to no data loss, while
        # a add/remove combo does.
        self.renamed_fields = {}

        for r in self.removed_fields:
            for a in self.added_fields:
                if self.old[r].type == self.new[a].type:
                    self.renamed_fields[r] = a

        self.added_fields = [
            f for f in self.added_fields
            if f not in set(self.renamed_fields.values())
        ]
        self.removed_fields = [
            f for f in self.removed_fields
            if f not in self.renamed_fields
        ]

    def detect_changed_fields(self):
        self.changed_fields = []

        for old in self.old:
            if old in self.renamed_fields:
                new = self.renamed_fields[old]
            elif old in self.new:
                new = old
            else:
                continue

            if self.old[old].required != self.new[new].required:
                self.changed_fields.append(new)

            elif self.old[old].type != self.new[new].type:
                self.changed_fields.append(new)
