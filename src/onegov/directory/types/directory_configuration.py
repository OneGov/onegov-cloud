from __future__ import annotations

import re
import yaml

from collections import defaultdict
from datetime import date, datetime, time
from more_itertools import collapse
from onegov.core.custom import json
from onegov.core.utils import normalize_for_url, safe_format, safe_format_keys
from onegov.form import parse_formcode, flatten_fieldsets, as_internal_id
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy_utils.types.scalar_coercible import ScalarCoercible
from urllib.parse import quote_plus


from typing import overload, Any, Literal, NoReturn, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from sqlalchemy.engine import Dialect
    from typing import Self, TypeVar

    _Base = TypeDecorator['DirectoryConfiguration']
    _MutableT = TypeVar('_MutableT', bound=Mutable)
else:
    _Base = TypeDecorator

# XXX i18n
SAFE_FORMAT_TRANSLATORS: dict[type[object], Callable[[Any], str]] = {
    date: lambda d: d.strftime('%d.%m.%Y'),
    datetime: lambda d: d.strftime('%d.%m.%Y %H:%M'),
    time: lambda t: t.strftime('%H:%M')
}


number_chunks = re.compile(r'([0-9]+)')


def pad_numbers_in_chunks(text: str, padding: int = 8) -> str:
    """ Alphanumeric sorting by padding all numbers.

    For example:
        foobar-1-to-10 becomes foobar-0000000001-to-0000000010)

    See:
        https://nedbatchelder.com/blog/200712/human_sorting.html

    """
    return ''.join(
        part.rjust(padding, '0') if part.isdigit() else part
        for part in number_chunks.split(text)
    )


class DirectoryConfigurationStorage(_Base, ScalarCoercible):

    impl = TEXT

    @property
    def python_type(self) -> type[DirectoryConfiguration]:
        return DirectoryConfiguration

    def process_bind_param(
        self,
        value: DirectoryConfiguration | None,
        dialect: Dialect
    ) -> str | None:

        if value is None:
            return None

        return value.to_json()

    def process_result_value(
        self,
        value: str | None,
        dialect: Dialect
    ) -> DirectoryConfiguration | None:

        if value is None:
            return None

        return DirectoryConfiguration.from_json(value)


class StoredConfiguration:

    fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.fields
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_yaml(self) -> str:
        text = yaml.dump(self.to_dict(), default_flow_style=False)
        return text.replace('\n- ', '\n  - ')

    @classmethod
    def from_json(cls, text: str) -> Self:
        return cls(**json.loads(text))

    @classmethod
    def from_yaml(cls, text: str) -> Self:
        return cls(**yaml.safe_load(text))


class DirectoryConfiguration(Mutable, StoredConfiguration):

    fields = (
        'title',
        'lead',
        'empty_notice',
        'order',
        'keywords',
        'searchable',
        'display',
        'direction',
        'link_pattern',
        'link_title',
        'link_visible',
        'thumbnail',
        'address_block_title',
        'show_as_thumbnails',
    )

    def __init__(
        self,
        # FIXME: title is not actually nullable
        title: str = None,  # type:ignore[assignment]
        lead: str | None = None,
        empty_notice: str | None = None,
        order: list[str] | None = None,
        keywords: list[str] | None = None,
        searchable: list[str] | None = None,
        display: dict[str, list[str]] | None = None,
        direction: Literal['asc', 'desc'] | None = None,
        link_pattern: str | None = None,
        link_title: str | None = None,
        link_visible: bool | None = None,
        thumbnail: str | None = None,
        address_block_title: str | None = None,
        show_as_thumbnails: list[str] | None = None,
        # FIXME: We should probably at least emit a warning or store the
        #        extra items somewhere, so we don't just silently ignore
        #        unexpected data in storage
        **kwargs: object
    ) -> None:

        self.title = title
        self.lead = lead
        self.empty_notice = empty_notice
        self.order = order
        self.keywords = keywords
        self.searchable = searchable
        self.display = display
        self.direction = direction
        self.link_pattern = link_pattern
        self.link_title = link_title
        self.link_visible = link_visible
        self.thumbnail = thumbnail
        self.address_block_title = address_block_title
        self.show_as_thumbnails = show_as_thumbnails

    def __setattr__(self, name: str, value: object) -> None:
        self.changed()  # type:ignore[no-untyped-call]
        return super().__setattr__(name, value)

    def missing_fields(self, formcode: str | None) -> dict[str, list[str]]:
        """ Takes the given formcode and returns a dictionary with missing
        fields per configuration field. If the return-value is falsy, the
        configuration is valid.

        For example::

            >>> cfg = DirectoryConfiguration(title='[Name]')
            >>> cfg.missing_fields('Title = ___')

            {'title': ['Name']}

        """
        formfields = tuple(flatten_fieldsets(parse_formcode(formcode)))
        known = {field.human_id for field in formfields}

        errors = defaultdict(list)

        for name in self.fields:
            if not getattr(self, name):
                continue

            # booleans
            if name == 'link_visible':
                continue

            if name in ('title', 'lead'):
                found = safe_format_keys(getattr(self, name))
            else:
                found = getattr(self, name)

            for id in found:
                if id not in known:
                    errors[name].append(id)

        return errors

    @overload
    @classmethod
    def coerce(  # type:ignore[overload-overlap]
        cls, key: str, value: _MutableT
    ) -> _MutableT: ...
    @overload
    @classmethod
    def coerce(cls, key: str, value: object) -> NoReturn: ...

    @classmethod
    def coerce(cls, key: str, value: object) -> object:
        if not isinstance(value, Mutable):
            raise TypeError()
        else:
            return value

    def join(
        self,
        data: Mapping[str, Any],
        attribute: str,
        separator: str = '\n'
    ) -> str:

        def render(value: object) -> str:
            if isinstance(value, (list, tuple)):
                return '\n'.join((v and str(v) or '').strip() for v in value)

            if isinstance(value, str):
                return value.strip()

            return str(value) if value else ''

        return separator.join(render(s) for s in (
            data.get(as_internal_id(key)) for key in getattr(self, attribute)
        ))

    def safe_format(self, fmt: str, data: Mapping[str, Any]) -> str:
        return safe_format(
            fmt, self.for_safe_format(data), adapt=as_internal_id)

    def for_safe_format(self, data: Mapping[str, Any]) -> dict[str, Any]:
        return {
            k: SAFE_FORMAT_TRANSLATORS.get(type(v), str)(v)
            for k, v in data.items()
            if (
                type(v) in (str, int, float)
                or type(v) in SAFE_FORMAT_TRANSLATORS
            )
        }

    def extract_name(self, data: Mapping[str, Any]) -> str:
        return normalize_for_url(self.extract_title(data))

    def extract_title(self, data: Mapping[str, Any]) -> str:
        return self.safe_format(self.title, data)

    def extract_lead(self, data: Mapping[str, Any]) -> str | None:
        return self.lead and self.safe_format(self.lead, data)

    def extract_link(self, data: Mapping[str, Any]) -> str | None:
        return self.link_pattern and self.safe_format(self.link_pattern, {
            k: quote_plus(v) for k, v in self.for_safe_format(data).items()
        })

    def extract_order(self, data: Mapping[str, Any]) -> str:
        # by default we use the title as order
        attribute = (
            (self.order and 'order')
            or (self.title and 'title')
        )
        order = normalize_for_url(self.join(data, attribute))
        order = pad_numbers_in_chunks(order)

        return order

    def extract_searchable(self, data: Mapping[str, Any]) -> str:
        # Remove non-searchable fields from data
        assert self.searchable is not None
        data = {as_internal_id(id): data.get(as_internal_id(id))
                for id in self.searchable}

        return self.join(data, 'searchable')

    def extract_keywords(self, data: Mapping[str, Any]) -> set[str] | None:
        if not self.keywords:
            return None

        keywords = set()

        for key in self.keywords:
            key = as_internal_id(key)

            for value in collapse(data.get(key, ())):
                if isinstance(value, str):
                    value = value.strip()

                if value:
                    keywords.add(f'{key}:{value}')

        return keywords


DirectoryConfiguration.associate_with(DirectoryConfigurationStorage)  # type:ignore[no-untyped-call]
