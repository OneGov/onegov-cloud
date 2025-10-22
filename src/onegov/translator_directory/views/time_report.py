from __future__ import annotations

from onegov.core.security import Secret
from onegov.translator_directory import TranslatorDirectoryApp, _
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.layout import DefaultLayout


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest


@TranslatorDirectoryApp.html(
    model=TimeReportCollection,
    template='time_reports.pt',
    permission=Secret,
)
def view_time_reports(
    self: TimeReportCollection,
    request: TranslatorAppRequest,
) -> RenderData:

    layout = DefaultLayout(request.app.org, request)

    return {
        'layout': layout,
        'model': self,
        'title': _('Time Reports'),
        'reports': self.batch,
    }
