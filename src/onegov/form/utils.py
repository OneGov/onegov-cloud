from __future__ import annotations

import hashlib
import re
import wtforms.widgets.core

from bs4 import BeautifulSoup
from decimal import Decimal
from unidecode import unidecode


from typing import cast, overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from bs4 import NavigableString, Tag
    from collections.abc import (
        Callable, Collection, Mapping, MutableSequence)
    from onegov.file.models import File
    from onegov.form import Form
    from typing import Self
    from wtforms.fields.core import UnboundField

    type _TagOrString = NavigableString | Tag


_unwanted_characters = re.compile(r'[^a-zA-Z0-9]+')
_html_tags = re.compile(r'<.*?>')

original_html_params = wtforms.widgets.core.html_params


def as_internal_id(label: str) -> str:
    clean = unidecode(label).strip(' "\'').lower()
    clean = _unwanted_characters.sub('_', clean)

    return clean


def get_fields_from_class(
    cls: type[Form]
) -> list[tuple[str, UnboundField[Any]]]:

    # often times FormMeta will have already calculated the fields
    # and stored them on the class, so we only need to calculate
    # them fresh if this attribute is None
    if cls._unbound_fields is not None:
        return cls._unbound_fields

    # FIXME: this is transcribed from FormMeta.__call__, so it is
    #        a little fragile, perhaps we can come up with a way
    #        to safely call it regardless of what __new__/__init__
    #        on cls looks like, so we can re-use their code.
    fields = [
        (name, field)
        for name in dir(cls)
        if not name.startswith('_')
        and hasattr((field := getattr(cls, name)), '_formfield')
    ]

    fields.sort(key=lambda x: (x[1].creation_counter, x[0]))

    return fields


# FIXME: What about html entities? i.e. &.*;
def extract_text_from_html(html: str) -> str:
    return _html_tags.sub('', html)


def disable_required_attribute_in_html_inputs() -> None:
    """ Replaces the required attribute with aria-required. """

    def patched_html_params(**kwargs: object) -> str:
        if kwargs.pop('required', None):
            kwargs['aria_required'] = True
        return original_html_params(**kwargs)

    wtforms.widgets.core.html_params = patched_html_params
    wtforms.widgets.core.Input.html_params = staticmethod(  # type:ignore
        patched_html_params)


class decimal_range:  # ruff:ignore[invalid-class-name]
    """ Implementation of Python's range builtin using decimal values instead
    of integers.

    """

    __slots__ = ('start', 'stop', 'step', 'current')

    def __init__(
        self,
        start: str | float | Decimal,
        stop: str | float | Decimal,
        step: str | float | Decimal | None = None
    ) -> None:

        self.start = self.current = Decimal(start)
        self.stop = Decimal(stop)
        if step is None:
            step = '1' if self.start <= self.stop else '-1'
        self.step = Decimal(step)

        assert self.step != Decimal(0)

    def __repr__(self) -> str:
        if (
            (self.start <= self.stop and self.step == Decimal('1.0'))
            or (self.start >= self.stop and self.step == Decimal('-1.0'))
        ):
            return f"decimal_range('{self.start}', '{self.stop}')"

        return f"decimal_range('{self.start}', '{self.stop}', '{self.step}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (
            self.start, self.stop, self.step
        ) == (
            other.start, other.stop, other.step
        )

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Decimal:
        result, self.current = self.current, self.current + self.step

        if self.step > 0 and result >= self.stop:
            raise StopIteration

        if self.step < 0 and result <= self.stop:
            raise StopIteration

        return result


def hash_definition(definition: str) -> str:
    return hashlib.new(  # nosec:B324
        'md5',
        definition.encode('utf-8'),
        usedforsecurity=False
    ).hexdigest()


@overload
def path_to_filename(path: None) -> None: ...
@overload
def path_to_filename(path: str) -> str: ...


def path_to_filename(path: str | None) -> str | None:
    if not path:
        return None
    if not isinstance(path, str):
        raise TypeError
    if '/' in path:
        return path.rsplit('/', 1)[-1]
    if '\\' in path:
        return path.rsplit('\\', 1)[-1]
    return path


def remove_empty_links(
    text: str,
    invisible_links: list[Tag] | None = None
) -> str:
    # Find links with no text or other tags
    # only br tags and/or whitespaces
    # if you pass in a list, the invisible links will be
    # appended to it
    soup = BeautifulSoup(str(text), 'html.parser')
    for link in soup.find_all('a'):
        if not any(
            tag.name != 'br' and not (
                tag.name is None and tag.isspace()
            )
            for tag in cast('list[_TagOrString]', link.contents)
        ):
            if invisible_links is not None:
                invisible_links.append(link)
            if all(
                tag.name == 'br'
                for tag in cast('list[_TagOrString]', link.contents)
            ):
                link.replace_with(
                    BeautifulSoup('<br/>', 'html.parser')
                )
            else:
                link.decompose()

    return str(soup)


def _file_meta(file: File) -> dict[str, Any]:
    """ The serialized ``@<id>`` reference for an already-stored file. """
    try:
        size = file.reference.file.content_length
    except OSError:
        size = -1
    return {
        'data': f'@{file.id}',
        'filename': file.name,
        'mimetype': file.reference.content_type,
        'size': size,
    }


def reconcile_uploaded_files[FileT: File](
    *,
    file_cls: type[FileT],
    fields: Mapping[str, Any],
    multiple: Collection[str],
    files: MutableSequence[FileT],
    delete: Callable[[FileT], None],
    flush: Callable[[], None] = lambda: None,  # noop
) -> dict[str, Any]:
    """ Reconciles the submitted upload fields against the already-stored
    files, shared by form submissions and directory entries so both decide
    which files to delete/insert/keep the exact same way.

    ``multiple`` holds the ids of the fields that accept more than one file
    (the caller knows this unambiguously); every other field is a single one,
    handled as a list of one slot.

    Stored files are matched by their ``note`` (``<field id>`` for a single
    field, ``<field id>:<index>`` for a multiple one). For each field, per
    slot, the file is kept (note renumbered to the new, compacted index),
    trashed, or replaced by a fresh upload.

    ``files`` is mutated in place (new files appended, removed ones passed to
    ``delete``); the new serialized values are returned keyed by field id.

    ``flush`` is called right after storing a new file, for callers that need
    it flushed before reading back its stored size (form submissions pass
    ``session.flush``); it defaults to a no-op since directory entries read the
    size without a flush.

    """
    from onegov.file.utils import (
        is_stored_file_reference, keep_stored_file, store_uploaded_file)

    files_by_note = {f.note: f for f in files}
    kept: set[int] = set()
    updated: dict[str, Any] = {}

    for field_id, field in fields.items():
        is_multiple = field_id in multiple
        subfields = list(field) if is_multiple else [field]

        new_idx = 0
        result: list[Any] = []
        for old_idx, slot in enumerate(subfields):
            note_key = f'{field_id}:{new_idx}' if is_multiple else field_id
            old_note = f'{field_id}:{old_idx}' if is_multiple else field_id

            action = getattr(slot, 'action', None)
            value = getattr(slot, 'data', None)
            has_upload = bool(getattr(slot, 'file', None)) and bool(
                getattr(slot, 'filename', None))

            if action == 'delete':
                continue

            # a fresh upload replaces the slot's stored file
            if has_upload and not is_stored_file_reference(value):
                new_file = store_uploaded_file(
                    file_cls, files, note_key, slot.file, slot.filename)
                flush()
                kept.add(id(new_file))
                result.append(_file_meta(new_file))
                new_idx += 1
                continue

            # keep the stored file (unchanged, kept, or an '@<id>' resend)
            if keep_stored_file(value, action):
                existing = files_by_note.get(old_note)
                if existing is None:
                    continue  # nothing stored to keep (e.g. a new slot)
                if existing.note != note_key:
                    existing.note = note_key
                kept.add(id(existing))
                result.append(_file_meta(existing))
                new_idx += 1

        updated[field_id] = (
            result if is_multiple else (result[0] if result else {})
        )

    # trash files owned by a processed field that are no longer kept
    for file in list(files):
        if id(file) in kept or file.note is None:
            continue
        base, sep, idx = file.note.rpartition(':')
        owner = base if sep and idx.isdigit() else file.note
        if owner in fields:
            delete(file)

    return updated
