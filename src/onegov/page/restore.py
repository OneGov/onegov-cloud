from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.page import Page
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import flag_modified


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class PageRestore:
    """Validate a snapshot before applying it to the selected tenant."""

    snapshots: list[dict[str, Any]]
    missing_files: list[str]

    @classmethod
    def prepare(
        cls,
        session: Session,
        snapshot: object,
        skip_missing_files: bool = False,
    ) -> PageRestore:
        snapshots: list[dict[str, Any]] = []
        ids: set[int] = set()
        locations: set[tuple[int | None, str]] = set()
        file_ids: set[str] = set()

        def collect(data: object, parent: int | None = None) -> None:
            if not isinstance(data, dict):
                raise TypeError('Each page snapshot must be a JSON object.')
            page_id = data.get('id')
            if type(page_id) is not int or page_id <= 0 or page_id in ids:
                raise ValueError('Page IDs must be unique positive integers.')
            ids.add(page_id)
            page_type = data.get('type')
            if not isinstance(page_type, str):
                raise TypeError('Page type must be a string.')
            mapper = inspect(Page).polymorphic_map.get(page_type)
            if mapper is None:
                raise ValueError(f'Unknown page type: {page_type!r}.')
            columns = set(mapper.column_attrs.keys())
            if columns - data.keys() or data.keys() - columns - {
                'children',
                'file_ids',
            }:
                raise ValueError(
                    f'Invalid snapshot fields for page {page_id}.'
                )
            parent_id = data['parent_id']
            if parent_id is not None and type(parent_id) is not int:
                raise ValueError(f'Invalid parent ID for page {page_id}.')
            if parent is not None and parent_id != parent:
                raise ValueError(f'Inconsistent parent for page {page_id}.')
            name = data['name']
            if not isinstance(name, str) or normalize_for_url(name) != name:
                raise ValueError(f'Invalid name for page {page_id}.')
            location = (parent_id, name)
            if location in locations:
                raise ValueError(f'Duplicate page location: {name}.')
            locations.add(location)
            files = data.get('file_ids')
            if not isinstance(files, list) or not all(
                isinstance(file_id, str) for file_id in files
            ):
                raise ValueError(f'Invalid file IDs for page {page_id}.')
            file_ids.update(files)
            snapshots.append(deepcopy(data))
            children = data.get('children', [])
            if not isinstance(children, list):
                raise TypeError(f'Invalid children for page {page_id}.')
            for child in children:
                collect(child, page_id)

        collect(snapshot)
        for data in snapshots:
            existing = session.get(Page, data['id'])
            if existing is not None and existing.type != data['type']:
                raise ValueError(f"Page {data['id']} has a different type.")
            parent_id = data['parent_id']
            if parent_id is not None and parent_id not in ids:
                parent = session.get(Page, parent_id)
                if parent is None:
                    raise ValueError(f'Missing parent page: {parent_id}.')
                while parent is not None:
                    if parent.id in ids:
                        raise ValueError('Restoration would create a cycle.')
                    parent = parent.parent
            elif data is snapshots[0] and parent_id in ids:
                raise ValueError('Restoration would create a cycle.')
            conflict = (
                session.query(Page)
                .filter(
                    Page.parent_id == parent_id,
                    Page.name == data['name'],
                    Page.id != data['id'],
                )
                .first()
            )
            if conflict is not None:
                raise ValueError(
                    f"Page {conflict.id} already uses name {data['name']!r}."
                )

        available = {
            file.id
            for file in session.query(File).filter(File.id.in_(file_ids))
        }
        missing = sorted(file_ids - available)
        if missing and not skip_missing_files:
            raise ValueError(f"Missing files: {', '.join(missing)}")
        return cls(snapshots, missing)

    def apply(self, session: Session) -> Page:
        pages: dict[int, Page] = {}
        with session.no_autoflush:
            for data in self.snapshots:
                page = session.get(Page, data['id'])
                if page is None:
                    page = Page.get_polymorphic_class(data['type'])(
                        title=data['title']
                    )
                    session.add(page)
                for key in inspect(type(page)).column_attrs.keys():
                    setattr(page, key, deepcopy(data[key]))
                if inspect(page).persistent:
                    flag_modified(page, 'modified')
                page.parent = pages.get(data['parent_id'])
                if page.parent is None and data['parent_id'] is not None:
                    page.parent = session.get(Page, data['parent_id'])
                page.files = (
                    session.query(File)
                    .filter(File.id.in_(data['file_ids']))
                    .all()
                )
                pages[page.id] = page
        session.flush()
        return pages[self.snapshots[0]['id']]
