from __future__ import annotations


from email_validator import validate_email
from enum import Enum
from onegov.core.cache import instance_lru_cache
from onegov.core.crypto import random_token
from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.utils import increment_name, normalize_for_url
from onegov.directory.errors import ValidationError
from onegov.directory.migration import DirectoryMigration
from onegov.directory.types import (
    DirectoryConfiguration, DirectoryConfigurationStorage)
from onegov.file import File, MultiAssociatedFiles
from onegov.file.utils import keep_stored_file, store_uploaded_file
from onegov.form.orm_types import Formcode
from onegov.form.parser import ParsedForm
from onegov.search import SearchableContent
from sedate import to_timezone
from sqlalchemy import and_, exists, func, text, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.orm import Mapped
from sqlalchemy_utils import aggregated
from translationstring import TranslationString
from uuid import uuid4, UUID
from wtforms import FieldList


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from builtins import type as _type  # type is shadowed in model
    from collections.abc import Mapping
    from onegov.form import Form
    from onegov.form.parser.core import (
        BasicParsedField, FileParsedField, ParsedField)
    from sqlalchemy.sql import ColumnElement
    from typing import type_check_only
    from .directory_entry import DirectoryEntry

    type InheritType = Literal[_Sentinel.INHERIT]

    @type_check_only
    class DirectoryEntryForm(Form):
        # original form code
        _source: str

        @property
        def mixed_data(self) -> dict[str, Any]: ...

        def populate_obj(  # type:ignore[override]
            self,
            obj: DirectoryEntry,
            directory_update: bool = True
        ) -> None: ...

        def process_obj(
            self,
            obj: DirectoryEntry  # type:ignore[override]
        ) -> None: ...


class _Sentinel(Enum):
    INHERIT = object()


INHERIT = _Sentinel.INHERIT


class DirectoryFile(File):
    __mapper_args__ = {'polymorphic_identity': 'directory'}

    if TYPE_CHECKING:
        # NOTE: this should always be exactly one entry, since we use
        #       a one-to-many relationship on DirectoryEntry. Technically
        #       it's possible to create a DirectoryFile, that isn't linked
        #       to any directory entry, but generally this shouldn't happen
        linked_directory_entries: Mapped[list[DirectoryEntry]]

    @property
    def directory_entry(self) -> DirectoryEntry | None:
        # we gracefully handle if there are no linked entries, even though
        # there should always be exactly one
        entries = self.linked_directory_entries
        return entries[0] if entries else None

    @property
    def access(self) -> str:
        # we don't want these files to show up in search engines
        return 'secret' if self.published else 'private'


class Directory(Base, ContentMixin, TimestampMixin,
                SearchableContent, MultiAssociatedFiles):
    """ A directory of entries that share a common data structure. For example,
    a directory of people, of emergency services or playgrounds.

    """

    __tablename__ = 'directories'

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Directories', domain='onegov.org')
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'}
    }

    @property
    def fts_public(self) -> bool:
        return False  # to be overridden downstream

    #: An interal id for references (not public)
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The public, unique name of the directory
    name: Mapped[str] = mapped_column(unique=True)

    #: The title of the directory
    title: Mapped[str]

    #: Describes the directory briefly
    lead: Mapped[str | None]

    #: The normalized title for sorting
    order: Mapped[str] = mapped_column(index=True)

    #: The polymorphic type of the directory
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    #: The data structure of the contained entries
    parsed_structure: Mapped[ParsedForm] = mapped_column(Formcode)

    #: The configuration of the contained entries
    configuration: Mapped[DirectoryConfiguration] = mapped_column(
        DirectoryConfigurationStorage
    )

    #: The number of entries in the directory
    @aggregated('entries', mapped_column(Integer, nullable=False, default=0))
    def count(self) -> ColumnElement[int]:
        return func.count(text('1'))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    entries: Mapped[list[DirectoryEntry]] = relationship(
        order_by='DirectoryEntry.order',
        back_populates='directory'
    )

    @hybrid_property
    def structure(self) -> str:
        """ The parsed form as a parsable string """
        return self.parsed_structure.formcode

    @structure.inplace.setter
    def _structure_setter(self, value: str) -> None:
        self.parsed_structure = ParsedForm.from_formcode(value)

    @structure.inplace.expression
    @classmethod
    def _structure_expression(cls) -> ColumnElement[str | None]:
        return cls.parsed_structure['source_code'].astext

    @property
    def entry_cls_name(self) -> str:
        return 'DirectoryEntry'

    @property
    def entry_cls(self) -> _type[DirectoryEntry]:
        return self.__class__.registry._class_registry[  # type:ignore
            self.entry_cls_name
        ]

    def add(
        self,
        values: dict[str, Any],
        type: str | InheritType = INHERIT
    ) -> DirectoryEntry:

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
        # NOTE: If we're part of a session, we need to add the entry to
        #       that same session. This no longer happens automagically
        #       through relationships in SQLAlchemy 2+
        if session := object_session(self):
            session.add(entry)

        return self.update(entry, values, set_name=True)

    def add_by_form(
        self,
        form: DirectoryEntryForm,
        type: str | InheritType = INHERIT
    ) -> DirectoryEntry:

        entry = self.add(form.mixed_data, type)

        # certain features, like mixin-forms require the form population
        # code to run - it ain't pretty but it avoids a lot of headaches
        form.populate_obj(entry, directory_update=False)

        return entry

    def update(
        self,
        entry: DirectoryEntry,
        values: Mapping[str, Any],
        set_name: bool = False,
        force_update: bool = False
    ) -> DirectoryEntry:

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

            def get_value_field_from_note(file_id: str) -> Any:
                id, __, idx = file_id.rpartition(':')
                if idx is None or not idx.isdigit():
                    return values[file_id]
                return values[id][int(idx)]

            # files which are not given or whose value is {} are removed
            # (this is in line with onegov.form's file upload field+widget)
            for file in entry.files:

                # this indicates that the file has been renamed
                if file.note is None or file.note not in known_file_ids:
                    continue

                value_field = get_value_field_from_note(file.note)
                if isinstance(value_field, dict):
                    continue

                keep = value_field is not None and keep_stored_file(
                    value_field.data,
                    getattr(value_field, 'action', None)
                )
                if not keep:
                    assert session is not None
                    session.delete(file)

            for field in self.file_fields:
                field_values = values[field.id]
                if not field_values:
                    updated[field.id] = field_values
                    continue
                # migrate files during an entry migration: a single file is
                # treated as a list of one slot
                if isinstance(field_values, (dict, list)):
                    updated[field.id] = field_values
                    slots = (
                        [field_values]
                        if isinstance(field_values, dict)
                        else field_values
                    )
                    assert session is not None
                    for slot in slots:
                        file_id = slot['data'].lstrip('@')
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
                                slot.update({'data': f'@{new.id}'})

                    continue
                # single and multiple fields share one code path: a single
                # file is treated as a list of one slot
                is_single = field.type == 'fileinput'
                subfields = [field_values] if is_single else list(field_values)

                old_stored = (entry.values or {}).get(field.id)
                if is_single:
                    old_values = (
                        [old_stored]
                        if isinstance(old_stored, dict) and old_stored
                        else []
                    )
                else:
                    old_values = old_stored or []

                new_idx = 0
                result: list[Any] = []
                for old_idx, subfield_values in enumerate(subfields):
                    note_key = (
                        field.id if is_single else f'{field.id}:{new_idx}'
                    )

                    # keep files if selected in the dialog
                    if getattr(subfield_values, 'action', None) == 'keep':
                        if len(old_values) > old_idx:
                            original = old_values[old_idx]
                            result.append(original)
                            # point file.note at the (possibly new) index
                            file_id = original['data'].lstrip('@')
                            for file in entry.files:
                                if file.id == file_id:
                                    if file.note != note_key:
                                        file.note = note_key
                                    break
                            new_idx += 1
                            continue
                        # new entry / added file: no stored file yet, fall
                        # through to create it from the resent upload below

                    # delete files if selected in the dialog
                    if getattr(subfield_values, 'action', None) == 'delete':
                        continue

                    # stale formdata guard: need both file and filename
                    if not getattr(subfield_values, 'file', None) or \
                            not getattr(subfield_values, 'filename', None):
                        continue

                    new_file = store_uploaded_file(
                        DirectoryFile, entry.files, note_key,
                        subfield_values.file, subfield_values.filename
                    )
                    result.append({
                        'data': '@' + new_file.id,
                        'filename': subfield_values.filename,
                        'mimetype': new_file.reference.file.content_type,
                        'size': new_file.reference.file.content_length
                    })
                    new_idx += 1

                updated[field.id] = (
                    (result[0] if result else {}) if is_single else result
                )

        # update the values
        if force_update or entry.values != updated:
            entry.values = updated

            # mark the values as dirty (required because values is only part
            # of the actual content dictionary)
            entry.content.changed()  # type:ignore[attr-defined]

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
                    existing = {
                        n for n, in session.query(
                            self.entry_cls.name
                        ).filter(
                            self.entry_cls.directory_id == self.id
                        )
                        if n != entry.name
                    }
                    while name in existing:
                        name = increment_name(name)
                    entry.name = name
            else:
                entry.name = name

        # validate the values
        form = self.form_obj
        form.process(data=entry.values)

        if not form.validate():

            # if the validation error is captured, the entry is added
            # to the directory, unless we expunge it
            entry.directory = None  # type: ignore[assignment]
            if session:
                session.expunge(entry)

            raise ValidationError(entry, form.errors)

        if session and not session._flushing:
            session.flush()

        return entry

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)

    @observes('parsed_structure', 'configuration')
    def structure_configuration_observer(
        self,
        parsed_structure: set[tuple[str, Any]],
        configuration: DirectoryConfiguration
    ) -> None:
        self.migration(self.parsed_structure, configuration).execute()

    def entry_with_name_exists(self, name: str) -> bool:
        session = object_session(self)
        assert session is not None
        return session.query(exists().where(and_(
            self.entry_cls.name == name,
            self.entry_cls.directory_id == self.id
        ))).scalar()

    def migration(
        self,
        new_structure: ParsedForm,
        new_configuration: DirectoryConfiguration | None
    ) -> DirectoryMigration:

        return DirectoryMigration(
            directory=self,
            new_structure=new_structure,
            new_configuration=new_configuration
        )

    @property
    def fields(self) -> tuple[ParsedField, ...]:
        return self.parsed_structure.flattened_fields

    @property
    def basic_fields(self) -> tuple[BasicParsedField, ...]:
        return tuple(
            f for f in self.fields
            if f.type != 'fileinput' and f.type != 'multiplefileinput'
        )

    @property
    def file_fields(self) -> tuple[FileParsedField, ...]:
        return tuple(
            f for f in self.fields
            if f.type == 'fileinput' or f.type == 'multiplefileinput'
        )

    def field_by_id(self, id: str) -> ParsedField | None:
        query = (f for f in self.fields if f.human_id == id or f.id == id)
        return next(query, None)

    @property
    def form_obj(self) -> DirectoryEntryForm:
        return self.form_obj_from_structure(self.parsed_structure)

    @property
    def form_class(self) -> _type[DirectoryEntryForm]:
        return self.form_class_from_structure(self.parsed_structure)

    @instance_lru_cache(maxsize=1)
    def form_obj_from_structure(
        self,
        structure: ParsedForm
    ) -> DirectoryEntryForm:
        return self.form_class_from_structure(structure)()

    @instance_lru_cache(maxsize=1)
    def form_class_from_structure(
        self,
        structure: ParsedForm
    ) -> _type[DirectoryEntryForm]:

        directory = self

        class DirectoryEntryForm(structure.form_class()):  # type:ignore

            @property
            def mixed_data(self) -> dict[str, Any]:
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

            def populate_obj(
                self,
                obj: DirectoryEntry,
                directory_update: bool = True
            ) -> None:

                # skip directory structure fields, directory.update()
                # handles those
                exclude = {f.id for f in directory.fields}

                super().populate_obj(obj, exclude=exclude)

                if directory_update:
                    directory.update(obj, self.mixed_data)

            def process_obj(self, obj: DirectoryEntry) -> None:
                super().process_obj(obj)

                for field in directory.fields:
                    form_field = getattr(self, field.id)

                    if form_field is None:
                        continue

                    data = obj.values.get(field.id)
                    if isinstance(form_field, FieldList):
                        for subdata in data or ():
                            form_field.append_entry(subdata)
                    else:
                        form_field.data = data

        return DirectoryEntryForm


class EntryRecipient(Base, TimestampMixin, ContentMixin):
    """ Represents a single recipient.
    """

    __tablename__ = 'entry_recipients'

    #: the id of the recipient, used in the url
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the email address of the recipient
    address: Mapped[str]

    @validates('address')
    def validate_address(self, key: str, address: str) -> str:
        assert validate_email(address)
        return address

    #: this token is used for confirm and unsubscribe
    token: Mapped[str] = mapped_column(default=random_token)

    #: when recipients are added, they are unconfirmed. At this point they get
    #: one e-mail with a confirmation link. If they ignore said e-mail they
    #: should not get another one.
    confirmed: Mapped[bool] = mapped_column(default=False)

    @property
    def subscription(self) -> EntrySubscription:
        return EntrySubscription(self, self.token)

    # FIXME: Add missing ForeignKey constraint (requires migration)
    directory_id: Mapped[UUID]

    @property
    def is_inactive(self) -> bool:
        """
        Checks if the directory entry recipient's email address is marked as
        inactive.

        Returns:
            bool: True if the email address is marked as inactive, False
            otherwise.
        """
        return self.meta.get('inactive', False)

    def mark_inactive(self) -> None:
        """
        Marks the recipient's email address as inactive.

        This method sets the 'inactive' flag in the recipient's metadata to
        True. It is typically used when a bounce event causes the email
        address to be deactivated by Postmark.
        """
        self.meta['inactive'] = True

    def reactivate(self) -> None:
        """
        Marks a previously `inactive` recipient as active again.
        """
        self.meta['inactive'] = False


class EntrySubscription:
    """ Adds subscription management to a recipient. """

    def __init__(self, recipient: EntryRecipient, token: str):
        self.recipient = recipient
        self.token = token

    @property
    def recipient_id(self) -> UUID:
        # even though this seems redundant, we need this property
        # for morepath, so it can match it to the path variable
        return self.recipient.id

    def confirm(self) -> bool:
        if self.recipient.token != self.token:
            return False

        self.recipient.confirmed = True
        return True

    def unsubscribe(self) -> bool:
        if self.recipient.token != self.token:
            return False

        session = object_session(self.recipient)
        assert session is not None
        session.delete(self.recipient)
        session.flush()

        return True
