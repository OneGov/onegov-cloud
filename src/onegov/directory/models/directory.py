import inspect

from sedate import to_timezone

from onegov.core.cache import instance_lru_cache
from onegov.core.cache import lru_cache
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.directory.errors import ValidationError, DuplicateEntryError
from onegov.directory.migration import DirectoryMigration
from onegov.directory.types import DirectoryConfigurationStorage
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.form import flatten_fieldsets, parse_formcode, parse_form
from onegov.search import SearchableContent
from sqlalchemy import Column
from sqlalchemy import func, exists, and_
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils import aggregated, observes
from uuid import uuid4
from wtforms import FieldList


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .directory_entry import DirectoryEntry


INHERIT = object()


class DirectoryFile(File):
    __mapper_args__ = {'polymorphic_identity': 'directory'}

    @property
    def access(self):
        # we don't want these files to show up in search engines
        return 'secret' if self.published else 'private'


class Directory(Base, ContentMixin, TimestampMixin, SearchableContent):
    """ A directory of entries that share a common data structure. For example,
    a directory of people, of emergency services or playgrounds.

    """

    __tablename__ = 'directories'

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'}
    }

    @property
    def es_public(self):
        return False  # to be overridden downstream

    #: An interal id for references (not public)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The public, unique name of the directory
    name = Column(Text, nullable=False, unique=True)

    #: The title of the directory
    title = Column(Text, nullable=False)

    #: Describes the directory briefly
    lead = Column(Text, nullable=True)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    #: The polymorphic type of the directory
    type = Column(Text, nullable=False, default=lambda: 'generic')

    #: The data structure of the contained entries
    structure = Column(Text, nullable=False)

    #: The configuration of the contained entries
    configuration = Column(DirectoryConfigurationStorage, nullable=False)

    #: The number of entries in the directory
    @aggregated('entries', Column(Integer, nullable=False, default=0))
    def count(self):
        return func.count('1')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    entries: 'relationship[list[DirectoryEntry]]' = relationship(
        'DirectoryEntry',
        order_by='DirectoryEntry.order',
        backref='directory'
    )

    @property
    def entry_cls_name(self):
        return 'DirectoryEntry'

    @property
    def entry_cls(self):
        return self.__class__._decl_class_registry[self.entry_cls_name]

    def add(self, values, type=INHERIT):
        start = values.pop('publication_start', None)
        end = values.pop('publication_end', None)

        # Not converting to UTC here led to returning non-UTC datetimes
        # from UTCDateTimeField, not triggering `def process_result_value`
        if start:
            start = to_timezone(start, 'UTC')
        if end:
            end = to_timezone(end, 'UTC')

        entry = self.entry_cls(
            directory=self,
            type=self.type if type is INHERIT else type,
            meta={},
            publication_start=start,
            publication_end=end,
        )

        return self.update(entry, values, set_name=True)

    def add_by_form(self, form, type=INHERIT):
        entry = self.add(form.mixed_data, type)

        # certain features, like mixin-forms require the form population
        # code to run - it ain't pretty but it avoids a lot of headaches
        form.populate_obj(entry, directory_update=False)

        return entry

    def update(self, entry, values, set_name=False, force_update=False):
        session = object_session(self)

        # replace all existing basic fields
        updated = {f.id: values[f.id] for f in self.basic_fields}

        # treat file fields differently
        known_file_ids = {
            f.id if idx is None else f'{f.id}:{idx}'
            for f in self.file_fields
            # add an id for each file in a multiple upload field
            for idx in (
                range(len(values[f.id]))
                if hasattr(values[f.id], '__len__')
                else [None]
            )
        }

        if self.file_fields:

            def get_value_field_from_note(file_id):
                id, __, idx = file_id.rpartition(':')
                if idx is None or not idx.isdigit():
                    return values[file_id]
                return values[id][int(idx)]

            # files which are not given or whose value is {} are removed
            # (this is in line with onegov.form's file upload field+widget)
            for f in entry.files:

                # this indicates that the file has been renamed
                if f.note not in known_file_ids:
                    continue

                value_field = get_value_field_from_note(f.note)
                if isinstance(value_field, dict):
                    continue

                delete = (
                    value_field is None
                    or value_field.data == {}
                    or value_field.data is not None
                )

                if delete:
                    session.delete(f)

            for field in self.file_fields:
                field_values = values[field.id]
                if not field_values:
                    updated[field.id] = field_values
                    continue
                # migrate files during an entry migration
                if isinstance(field_values, dict):
                    updated[field.id] = field_values
                    file_id = field_values['data'].lstrip('@')
                    with session.no_autoflush:
                        f = session.query(File).filter_by(id=file_id).first()
                        if f and f.type != 'directory':
                            new = DirectoryFile(
                                id=random_token(),
                                name=f.name,
                                note=f.note,
                                reference=f.reference
                            )
                            entry.files.append(new)
                            updated[field.id].update({'data': f'@{new.id}'})

                    continue
                elif isinstance(field_values, list):
                    updated[field.id] = field_values
                    for idx, field_value in enumerate(field_values):
                        file_id = field_value['data'].lstrip('@')
                        with session.no_autoflush:
                            f = session.query(File).filter_by(
                                id=file_id
                            ).first()
                            if f and f.type != 'directory':
                                new = DirectoryFile(
                                    id=random_token(),
                                    name=f.name,
                                    note=f.note,
                                    reference=f.reference
                                )
                                entry.files.append(new)
                                updated[field.id][idx].update(
                                    {'data': f'@{new.id}'}
                                )

                    continue
                elif field.type == 'fileinput':
                    # keep files if selected in the dialog
                    if getattr(field_values, 'action', None) == 'keep':
                        original = (entry.values or {}).get(field.id, {})
                        updated[field.id] = original
                        continue

                    # delete files if selected in the dialog
                    if getattr(field_values, 'action', None) == 'delete':
                        updated[field.id] = {}
                        continue

                    # if there was no file supplied, we can't add it
                    if not getattr(field_values, 'file', None):
                        updated[field.id] = {}
                        continue

                    # create a new file
                    new_file = DirectoryFile(
                        id=random_token(),
                        name=field_values.filename,
                        note=field.id,
                        reference=as_fileintent(
                            content=field_values.file,
                            filename=field_values.filename
                        )
                    )
                    entry.files.append(new_file)

                    # keep a reference to the file in the values
                    updated[field.id] = {
                        'data': '@' + new_file.id,
                        'filename': field_values.filename,
                        'mimetype': new_file.reference.file.content_type,
                        'size': new_file.reference.file.content_length
                    }
                    continue

                # FIXME: there's quite a bit of copy pasta between the
                #        filefield and multiplefilefield case, we should
                #        try to refactor this so we can handle both more
                #        easily
                new_idx = 0
                updated[field.id] = []
                for old_idx, subfield_values in enumerate(field_values):
                    old_values = (entry.values or {}).get(field.id) or []

                    # keep files if selected in the dialog
                    if getattr(subfield_values, 'action', None) == 'keep':
                        if len(old_values) <= old_idx:
                            # it doesn't exist so we can't keep it
                            continue

                        original = old_values[old_idx]
                        updated[field.id].append(original)
                        # update the file.note so it points to the correct
                        # index in the list if necessary
                        file_id = original['data'].lstrip('@')
                        for file in entry.files:
                            if file.id == file_id:
                                new_key = f'{field.id}:{new_idx}'
                                if file.note != new_key:
                                    file.note = new_key
                                break
                        new_idx += 1
                        continue

                    # delete files if selected in the dialog
                    if getattr(subfield_values, 'action', None) == 'delete':
                        continue

                    # if there was no file supplied, we can't add it
                    if not getattr(subfield_values, 'file', None):
                        continue

                    # create a new file
                    new_file = DirectoryFile(
                        id=random_token(),
                        name=subfield_values.filename,
                        note=f'{field.id}:{new_idx}',
                        reference=as_fileintent(
                            content=subfield_values.file,
                            filename=subfield_values.filename
                        )
                    )
                    entry.files.append(new_file)

                    # keep a reference to the file in the values
                    updated[field.id].append({
                        'data': '@' + new_file.id,
                        'filename': subfield_values.filename,
                        'mimetype': new_file.reference.file.content_type,
                        'size': new_file.reference.file.content_length
                    })
                    new_idx += 1

        # update the values
        if force_update or entry.values != updated:
            entry.values = updated

            # mark the values as dirty (required because values is only part
            # of the actual content dictionary)
            entry.content.changed()

        # update the metadata
        for attr in ('title', 'lead', 'order', 'keywords'):
            new = getattr(self.configuration, f'extract_{attr}')(values)

            if new != getattr(entry, attr):
                setattr(entry, attr, new)

        # update the title
        if set_name:
            name = self.configuration.extract_name(values)

            if session:
                with session.no_autoflush:
                    if self.entry_with_name_exists(name):
                        entry.directory = None
                        session.expunge(entry)
                        raise DuplicateEntryError(name)

            entry.name = name

        # validate the values
        form = self.form_obj
        form.process(data=entry.values)

        if not form.validate():

            # if the validation error is captured, the entry is added
            # to the directory, unless we expunge it
            entry.directory = None
            session and session.expunge(entry)

            raise ValidationError(entry, form.errors)

        if session and not session._flushing:
            session.flush()

        return entry

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)

    @observes('structure', 'configuration')
    def structure_configuration_observer(self, structure, configuration):
        self.migration(structure, configuration).execute()

    def entry_with_name_exists(self, name):
        return object_session(self).query(exists().where(and_(
            self.entry_cls.name == name,
            self.entry_cls.directory_id == self.id
        ))).scalar()

    def migration(self, new_structure, new_configuration):
        return DirectoryMigration(
            directory=self,
            new_structure=new_structure,
            new_configuration=new_configuration
        )

    @property
    def fields(self):
        return self.fields_from_structure(self.structure)

    @staticmethod
    @lru_cache(maxsize=1)
    def fields_from_structure(structure):
        return tuple(flatten_fieldsets(parse_formcode(structure)))

    @property
    def basic_fields(self):
        return tuple(
            f for f in self.fields
            if f.type not in ('fileinput', 'multiplefileinput')
        )

    @property
    def file_fields(self):
        return tuple(
            f for f in self.fields
            if f.type in ('fileinput', 'multiplefileinput')
        )

    def field_by_id(self, id):
        query = (f for f in self.fields if f.human_id == id or f.id == id)
        return next(query, None)

    @property
    def form_obj(self):
        return self.form_obj_from_structure(self.structure)

    @property
    def form_class(self):
        return self.form_class_from_structure(self.structure)

    @instance_lru_cache(maxsize=1)
    def form_obj_from_structure(self, structure):
        return self.form_class_from_structure(structure)()

    @instance_lru_cache(maxsize=1)
    def form_class_from_structure(self, structure):
        directory = self

        class DirectoryEntryForm(parse_form(self.structure)):

            @property
            def mixed_data(self):
                # use the field data for non-file fields
                data = {
                    k: v for k, v in self.data.items() if k not in {
                        f.id for f in directory.file_fields
                    }
                }

                # use the field objects for file-fields
                for field in directory.file_fields:
                    data[field.id] = self[field.id]

                return data

            def populate_obj(self, obj, directory_update=True):
                exclude = {k for k, v in inspect.getmembers(
                    obj.__class__,
                    lambda v: isinstance(v, InstrumentedAttribute)
                )}

                include = ('publication_start', 'publication_end')
                exclude = {k for k in exclude if k not in include}

                super().populate_obj(obj, exclude=exclude)

                if directory_update:
                    directory.update(obj, self.mixed_data)

            def process_obj(self, obj):
                super().process_obj(obj)

                for field in directory.fields:
                    form_field = getattr(self, field.id)

                    if form_field is None:
                        continue

                    data = obj.values.get(field.id)
                    if isinstance(form_field, FieldList):
                        for subdata in data:
                            form_field.append_entry(subdata)
                    else:
                        form_field.data = data

        return DirectoryEntryForm
