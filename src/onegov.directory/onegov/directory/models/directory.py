import inspect

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


INHERIT = object()


class DirectoryFile(File):
    __mapper_args__ = {'polymorphic_identity': 'directory'}


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
    type = Column(Text, nullable=True)

    #: The data structure of the contained entries
    structure = Column(Text, nullable=False)

    #: The configuration of the contained entries
    configuration = Column(DirectoryConfigurationStorage, nullable=False)

    #: The number of entries in the directory
    @aggregated('entries', Column(Integer, nullable=False, default=0))
    def count(self):
        return func.count('1')

    __mapper_args__ = {
        'order_by': order,
        'polymorphic_on': type
    }

    entries = relationship(
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
        entry = self.entry_cls(
            directory=self,
            type=self.type if type is INHERIT else type,
            meta={},
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
        known_file_ids = {f.id for f in self.file_fields}

        if self.file_fields:

            # files which are not given or whose value is {} are removed
            # (this is in line with onegov.form's file upload field+widget)
            for f in entry.files:

                # this indicates that the file has been renamed
                if f.note not in known_file_ids:
                    continue

                if isinstance(values[f.note], dict):
                    continue

                delete = (
                    f.note not in values
                    or values[f.note] is None
                    or values[f.note].data == {}
                    or values[f.note].data is not None
                )

                if delete:
                    session.delete(f)

            for field in self.file_fields:
                # migrate files during an entry migration
                if values[field.id] is None or\
                        isinstance(values[field.id], dict):

                    updated[field.id] = values[field.id]
                    continue

                # keep files if selected in the dialog
                if getattr(values[field.id], 'action', None) == 'keep':
                    updated[field.id] = entry.values[field.id]
                    continue

                # delete files if selected in the dialog
                if getattr(values[field.id], 'action', None) == 'delete':
                    updated[field.id] = {}
                    continue

                # if there was no file supplied, we can't add it
                if not getattr(values[field.id], 'file', None):
                    updated[field.id] = {}
                    continue

                # create a new file
                new_file = DirectoryFile(
                    id=random_token(),
                    name=values[field.id].filename,
                    note=field.id,
                    reference=as_fileintent(
                        content=values[field.id].file,
                        filename=values[field.id].filename
                    )
                )
                entry.files.append(new_file)

                # keep a reference to the file in the values
                updated[field.id] = {
                    'data': '@' + new_file.id,
                    'filename': values[field.id].filename,
                    'mimetype': new_file.reference.file.content_type,
                    'size': new_file.reference.file.content_length
                }

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

            # if the validaiton error is captured, the entry is added
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
        self.name = self.name or self.order

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

    @lru_cache(maxsize=1)
    def fields_from_structure(self, structure):
        return tuple(flatten_fieldsets(parse_formcode(structure)))

    @property
    def basic_fields(self):
        return tuple(f for f in self.fields if f.type != 'fileinput')

    @property
    def file_fields(self):
        return tuple(f for f in self.fields if f.type == 'fileinput')

    def field_by_id(self, id):
        query = (f for f in self.fields if f.human_id == id or f.id == id)
        return next(query, None)

    @property
    def form_obj(self):
        return self.form_obj_from_structure(self.structure)

    @property
    def form_class(self):
        return self.form_class_from_structure(self.structure)

    @lru_cache(maxsize=1)
    def form_obj_from_structure(self, structure):
        return self.form_class_from_structure(structure)()

    @lru_cache(maxsize=1)
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

                super().populate_obj(obj, exclude=exclude)

                if directory_update:
                    directory.update(obj, self.mixed_data)

            def process_obj(self, obj):
                super().process_obj(obj)

                for field in directory.fields:
                    form_field = getattr(self, field.id)
                    form_field.data = obj.values.get(field.id)

        return DirectoryEntryForm
