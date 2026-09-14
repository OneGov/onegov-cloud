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
    files, shared by form submissions and directory entries. Follows the shape
    of the original form-submission update: compute ``files_to_add``/
    ``files_to_keep`` (and their multiple-field counterparts), trash what is no
    longer kept, then store the new single- and multiple-file uploads.

    ``multiple`` holds the ids of the multi-file fields. Stored files are
    matched by ``note`` (``<field id>`` single, ``<field id>:<index>`` multi).
    ``files`` is mutated in place; ``flush`` runs after storing a new file
    (form submissions pass ``session.flush``); the new values are returned.

    """
    from onegov.file.utils import (
        is_stored_file_reference, store_uploaded_file)

    # on a plain 'keep' the field carries no data (directories), so fall back
    # to the value bound as object_data
    def serialized(slot: Any) -> Any:
        value = getattr(slot, 'data', None)
        if value is None:
            value = getattr(slot, 'object_data', None)
        return value

    data: dict[str, Any] = {}
    for field_id, field in fields.items():
        if field_id in multiple:
            data[field_id] = [serialized(sub) for sub in field]
        else:
            data[field_id] = serialized(field)

    # single fields present (value != {}), split by fresh upload vs '@<id>' ref
    single_files = {
        field_id for field_id in fields
        if field_id not in multiple and data.get(field_id) != {}
    }
    files_to_add = {
        id for id in single_files
        if (file_meta := data.get(id))
        and not is_stored_file_reference(file_meta)
    }
    files_to_keep = single_files - files_to_add

    multi_files = {
        field_id: [
            index
            for index, value in enumerate(data.get(field_id, []))
            if value != {}
        ]
        for field_id in multiple
    }
    # a kept file is None (unchanged) or an '@<id>' resend
    multi_files_to_keep = {
        f'{id}:{idx}'
        for id, indeces in multi_files.items()
        if (file_metas := data.get(id))
        for idx in indeces
        if file_metas[idx] is None or is_stored_file_reference(file_metas[idx])
    }
    files_to_keep |= multi_files_to_keep

    files_by_note = {f.note: f for f in files}
    updated: dict[str, Any] = {}

    # trash files owned by a processed field that are no longer kept
    for file in list(files):
        if file.note is None or file.note in files_to_keep:
            continue
        base, sep, idx = file.note.rpartition(':')
        owner = base if sep and idx.isdigit() else file.note
        if owner in fields:
            delete(file)

    for field_id in single_files:
        if field_id in files_to_add:
            field = fields[field_id]
            # outdated formdata may lack a real file/filename; skip it
            if not getattr(field, 'file', None) or not getattr(
                field, 'filename', None
            ):
                updated[field_id] = {}
                continue
            new_file = store_uploaded_file(
                file_cls, files, field_id, field.file, field.filename)
            flush()
            updated[field_id] = _file_meta(new_file)
        else:
            existing = files_by_note.get(field_id)
            updated[field_id] = (
                _file_meta(existing) if existing is not None else {}
            )

    # explicitly cleared single fields (value == {})
    for field_id in fields:
        if field_id not in multiple and field_id not in single_files:
            updated[field_id] = {}

    for field_id, indeces in multi_files.items():
        subfields = list(fields[field_id])
        datalist = []
        new_idx = 0
        for old_idx in indeces:
            value = data[field_id][old_idx]
            old_key = f'{field_id}:{old_idx}'
            new_key = f'{field_id}:{new_idx}'
            if old_key in multi_files_to_keep:
                existing = files_by_note.get(old_key)
                if existing is not None:
                    if old_idx != new_idx:  # renumber the note
                        existing.note = new_key
                    value = _file_meta(existing)
            else:
                slot = subfields[old_idx]
                # skip subfields without a real file/filename (outdated data)
                if not getattr(slot, 'file', None) or not getattr(
                    slot, 'filename', None
                ):
                    continue
                new_file = store_uploaded_file(
                    file_cls, files, new_key, slot.file, slot.filename)
                flush()
                value = _file_meta(new_file)

            datalist.append(value)
            new_idx += 1

        updated[field_id] = datalist

    return updated
