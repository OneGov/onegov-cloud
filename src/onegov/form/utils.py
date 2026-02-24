from __future__ import annotations

import hashlib
import re
import wtforms.widgets.core

from decimal import Decimal
from bs4 import BeautifulSoup
from unidecode import unidecode


from typing import overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from typing import Self
    from wtforms.fields.core import UnboundField


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


class decimal_range:  # noqa: N801
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


def remove_empty_links(text: str) -> str:
    # Find links with no text or other tags
    # only br tags and/or whitespaces
    soup = BeautifulSoup(str(text), 'html.parser')
    for link in soup.find_all('a'):
        if not any(
            tag.name != 'br' and (
                tag.name or not tag.isspace()
            ) for tag in link.contents
        ):
            if all(tag.name == 'br' for tag in link.contents):
                link.replace_with(
                    BeautifulSoup('<br/>', 'html.parser')
                )
            else:
                link.decompose()

    return str(soup)
