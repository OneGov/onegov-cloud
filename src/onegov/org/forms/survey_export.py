from __future__ import annotations

from onegov.form import merge_forms
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from onegov.org.forms.generic import ExportForm
from operator import attrgetter


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest

    class SurveySubmissionsExportBase(ExportForm):
        pass
else:
    SurveySubmissionsExportBase = merge_forms(ExportForm)


class SurveySubmissionsExport(SurveySubmissionsExportBase):

    if TYPE_CHECKING:
        request: OrgRequest

    submission_window = MultiCheckboxField(
        label=_('Submission Window'),
        choices=None,
    )

    def on_request(self) -> None:
        if self.submission_window.choices is None:
            self.load_submission_window()  # type:ignore[unreachable]

    def load_submission_window(self) -> None:
        # FIXME: circular import - a layout class just to get a date format?
        from onegov.org.layout import DefaultLayout

        layout = DefaultLayout(self.model, self.request)

        windows = sorted(
            self.model.submission_windows,
            key=attrgetter('start')
        )

        if not windows:
            self.hide(self.submission_window)
            return

        self.submission_window.choices = [
            (window.id.hex,
             (f'{layout.format_date_range(window.start, window.end)}, '
             f'{window.title}'))
            for window in windows
        ]

        if self.request.params.get('submission_window_id'):
            self.submission_window.data = [
                self.request.params['submission_window_id']]
