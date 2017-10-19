import inspect

from onegov.core.cache import lru_cache
from onegov.core.crypto import random_token
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.directory.errors import ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.directory.types import DirectoryConfigurationStorage
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.form import flatten_fieldsets, parse_formcode, parse_form
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy_utils import observes
from uuid import uuid4


INHERIT = object()


class DirectoryFile(File):
    __mapper_args__ = {'polymorphic_identity': 'directory'}


class Directory(Base, ContentMixin, TimestampMixin, ORMSearchable):
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

    def add(self, values, type=INHERIT, form=None):
        entry = self.entry_cls(
            directory=self,
            type=self.type if type is INHERIT else type
        )

        object_session(self).add(entry)

        return self.update(entry, values, set_name=True)

    def add_by_form(self, form, type=INHERIT):
        entry = self.add(form.mixed_data, type)

        # certain features, like mixin-forms require the form population
        # code to run - it ain't pretty but it avoids a lot of headaches
        form.populate_obj(entry, directory_update=False)

        return entry

    def update(self, entry, values, set_name=False):
        session = object_session(self)

        # replace all existing basic fields
        updated = {f.id: values[f.id] for f in self.basic_fields}

        # treat file fields differently
        if self.file_fields:

            # files which are not given or whose value is {} are removed
            # (this is in line with onegov.form's file upload field+widget)
            for f in entry.files:

                # migration
                if isinstance(values[f.note], dict):
                    continue

                delete = (
                    f.note not in values or
                    values[f.note].data == {} or
                    values[f.note].data is not None
                )

                if delete:
                    session.delete(f)

            for field in self.file_fields:

                # migrate files during an entry migration
                if isinstance(values[field.id], dict):
                    updated[field.id] = values[field.id]
                    continue

                # keep files if selected in the dialog
                if values[field.id].data is None:
                    updated[field.id] = entry.values[field.id]
                    continue

                # delete files if selected in the dialog
                if not values[field.id].data:
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
                session.add(new_file)

                entry.files.append(new_file)

                # keep a reference to the file in the values
                updated[field.id] = {
                    'data': '@' + new_file.id,
                    'filename': values[field.id].filename,
                    'mimetype': new_file.reference.file.content_type,
                    'size': new_file.reference.file.content_length
                }

        # update the values
        entry.values = updated

        # update the metadata
        entry.title = self.configuration.extract_title(values)
        entry.lead = self.configuration.extract_lead(values)
        entry.order = self.configuration.extract_order(values)
        entry.keywords = self.configuration.extract_keywords(values)

        # update the title
        if set_name:
            entry.name = normalize_for_url(entry.title)

        # validate the values
        form = self.form_class(data=entry.values)

        if not form.validate():
            raise ValidationError(form.errors)

        # mark the values as dirty (required because values is only part
        # of the actual content dictionary)
        entry.content.changed()

        if not session._flushing:
            session.flush()

        return entry

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)
        self.name = self.name or self.order

    @observes('structure', 'configuration')
    def structure_configuration_observer(self, structure, configuration):
        migration = DirectoryMigration(
            directory=self,
            new_structure=structure,
            new_configuration=configuration
        )
        migration.execute()

    @property
    def fields(self):
        return tuple(flatten_fieldsets(parse_formcode(self.structure)))

    @property
    def basic_fields(self):
        return tuple(f for f in self.fields if f.type != 'fileinput')

    @property
    def file_fields(self):
        return tuple(f for f in self.fields if f.type == 'fileinput')

    @property
    def form_class(self):
        return self.form_class_from_structure(self.structure)

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
