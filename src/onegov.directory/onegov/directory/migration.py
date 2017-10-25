from onegov.form import as_internal_id
from onegov.form import flatten_fieldsets
from onegov.form import parse_form
from onegov.form import parse_formcode
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.attributes import get_history


class DirectoryMigration(object):
    """ Takes a directory and the structure/configuration it should have in
    the future.

    It then migrates the existing directory entries, if possible.

    """

    def __init__(self, directory, new_structure, new_configuration):

        self.directory = directory
        self.new_structure = new_structure
        self.new_configuration = new_configuration
        self.new_form_class = parse_form(new_structure)
        self.fieldtype_migrations = FieldTypeMigrations()

        self.changes = StructuralChanges(
            self.old_structure,
            self.new_structure
        )

    @property
    def old_structure(self):
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

            # we can change a required field to a non-required
            if old.required and not new.required and old.type == new.type:
                continue

            # we cannot introduce a required field after the fact
            # XXX -> we can make this work by validating the results first
            if new.required and not old.required:
                break

            # we can only convert certain types
            if old.required == new.required and old.type != new.type:
                if not self.fieldtype_migrations.possible(old.type, new.type):
                    break
        else:
            return True

        return False

    def execute(self):
        assert self.possible

        self.directory.structure = self.new_structure
        self.directory.configuration = self.new_configuration

        for entry in self.directory.entries:
            # XXX this is currently rather destructive and automatic, we would
            # want to change this into something that is save for the user
            # by maybe keeping the old values around somehow
            for added in self.changes.added_fields:
                added = as_internal_id(added)
                entry.values[added] = None

            for removed in self.changes.removed_fields:
                removed = as_internal_id(removed)
                del entry.values[removed]

            for old, new in self.changes.renamed_fields.items():
                old_human, new_human = old, new
                old, new = as_internal_id(old), as_internal_id(new)
                entry.values[new] = entry.values[old]
                del entry.values[old]

                self.directory.configuration.rename_field(old_human, new_human)

            for changed in self.changes.changed_fields:
                changed = as_internal_id(changed)
                convert = self.fieldtype_migrations.get_converter(
                    self.changes.old[changed].type,
                    self.changes.new[changed].type
                )

                entry.values[changed] = convert(entry.values[changed])

            self.directory.update(entry, entry.values)

            # force an elasticsearch reindex
            flag_modified(entry, 'title')


class FieldTypeMigrations(object):
    """ Contains methods to migrate fields from one type to another. """

    def possible(self, old_type, new_type):
        return self.get_converter(old_type, new_type) is not None

    def get_converter(self, old_type, new_type):

        if old_type == 'password':
            return  # disabled to avoid accidental leaks

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

    def date_to_text(self, value):
        return '{:%d.%m.%Y}'.format(value)

    def datetime_to_text(self, value):
        return '{:%d.%m.%Y %H:%M}'.format(value)

    def time_to_text(self, value):
        return '{:%H:%M}'.format(value)


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
            self.added_fields or
            self.removed_fields or
            self.renamed_fields or
            self.changed_fields
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
            f for f in self.added_fields if f not in self.renamed_fields]
        self.removed_fields = [
            f for f in self.removed_fields if f not in self.renamed_fields]

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
