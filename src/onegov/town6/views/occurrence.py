""" The onegov org collection of images uploaded to the site. """
from __future__ import annotations

from onegov.core.security import Public, Private, Secret

from onegov.event import Occurrence, OccurrenceCollection
from onegov.org.forms.event import EventConfigurationForm
from onegov.town6.layout import OccurrenceLayout
from onegov.org.views.occurrence import (
    view_occurrences, view_occurrence, export_occurrences,
    import_occurrences, handle_edit_event_filters)
from onegov.town6 import TownApp
from onegov.org.forms import ExportForm, EventImportForm
from onegov.town6.layout import OccurrencesLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=OccurrenceCollection,
    template='occurrences.pt',
    permission=Public
)
def town_view_occurrences(
    self: OccurrenceCollection,
    request: TownRequest
) -> RenderData:
    return view_occurrences(self, request, OccurrencesLayout(self, request))


@TownApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def town_view_occurrence(
    self: Occurrence,
    request: TownRequest
) -> RenderData:
    layout = OccurrenceLayout(self, request)
    request.include('monthly-view')
    return view_occurrence(self, request, layout)


@TownApp.form(
    model=OccurrenceCollection,
    name='edit',
    template='directory_form.pt',
    permission=Secret,
    form=EventConfigurationForm
)
def town_handle_edit_event_filters(
    self: OccurrenceCollection,
    request: TownRequest,
    form: EventConfigurationForm
) -> RenderData | Response:
    layout = OccurrencesLayout(self, request)
    return handle_edit_event_filters(self, request, form, layout)


@TownApp.form(
    model=OccurrenceCollection,
    name='export',
    permission=Private,
    form=ExportForm,
    template='export.pt'
)
def town_export_occurrences(
    self: OccurrenceCollection,
    request: TownRequest,
    form: ExportForm
) -> RenderData | Response:
    return export_occurrences(
        self, request, form, OccurrencesLayout(self, request))


@TownApp.form(
    model=OccurrenceCollection,
    name='import',
    permission=Private,
    form=EventImportForm,
    template='form.pt'
)
def town_import_occurrences(
    self: OccurrenceCollection,
    request: TownRequest,
    form: EventImportForm
) -> RenderData | Response:
    return import_occurrences(
        self, request, form, OccurrencesLayout(self, request))
