from __future__ import annotations

from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.winterthur import WinterthurApp
from onegov.org.views import directory as base
from onegov.directory import DirectoryCollection
from onegov.core.security import Secret
from onegov.form import merge_forms
from onegov.form.utils import get_fields_from_class


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import DirectoryForm
    from onegov.org.models import ExtendedDirectory
    from onegov.winterthur.request import WinterthurRequest
    from webob import Response


def get_directory_form_class(
    model: DirectoryCollection[Any] | ExtendedDirectoryEntryCollection,
    request: WinterthurRequest
) -> type[DirectoryForm]:
    forms = [base.get_directory_form_class(model, request)]
    registry = request.app.config.directory_search_widget_registry

    widget_fields = {}

    for name, cls in registry.items():
        if hasattr(cls, 'form'):
            widget_fields[name] = tuple(
                n for n, _ in get_fields_from_class(cls.form)
            )
            forms.append(cls.form)

    class AdaptedDirectoryForm(merge_forms(*forms)):  # type:ignore[misc]

        def populate_obj(
            self,
            obj: ExtendedDirectory,
            *args: Any,
            **kwargs: Any
        ) -> None:
            nonlocal widget_fields

            super().populate_obj(obj, *args, **kwargs)

            obj.search_widget_config = config = {}

            for name, fields in widget_fields.items():
                config[name] = {f: self.data[f] for f in fields}

        def process_obj(self, obj: ExtendedDirectory) -> None:
            nonlocal widget_fields

            super().process_obj(obj)

            if not obj.search_widget_config:
                return

            for name, fields in widget_fields.items():
                if name not in obj.search_widget_config:
                    continue

                for f in fields:
                    self[f].data = obj.search_widget_config[name].get(f)

    return AdaptedDirectoryForm


@WinterthurApp.form(
    model=DirectoryCollection, name='new', template='form.pt',
    permission=Secret, form=get_directory_form_class
)
def handle_new_directory(
    self: DirectoryCollection[Any],
    request: WinterthurRequest,
    form: DirectoryForm
) -> RenderData | Response:
    return base.handle_new_directory(self, request, form)


@WinterthurApp.form(
    model=ExtendedDirectoryEntryCollection, name='edit',
    template='directory_form.pt', permission=Secret,
    form=get_directory_form_class
)
def handle_edit_directory(
    self: ExtendedDirectoryEntryCollection,
    request: WinterthurRequest,
    form: DirectoryForm
) -> RenderData | Response:
    return base.handle_edit_directory(self, request, form)
