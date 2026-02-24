from __future__ import annotations

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.form import Form
    from onegov.org.app import OrgApp
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Session


class ExportCollection:

    def __init__(
        self,
        app: OrgApp,
        registry: str = 'export_registry'
    ) -> None:
        self.registry = getattr(app.config, registry)

    def by_id(self, id: object) -> Export | None:
        return self.registry.get(id)

    def exports_for_current_user(
        self,
        request: OrgRequest
    ) -> Iterator[Export]:
        app = request.app

        for export in self.registry.values():
            if request.has_permission(export, app.permission_by_view(export)):
                yield export


class Export:

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    if TYPE_CHECKING:
        def __getattr__(self, name: str) -> Any: ...

    def run(
        self,
        form: Form,
        session: Session
    ) -> Iterable[Iterable[tuple[Any, Any]]]:
        raise NotImplementedError
