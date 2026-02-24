from __future__ import annotations

from onegov.form import merge_forms
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from onegov.org.forms.generic import DateRangeForm, ExportForm
from operator import attrgetter
from wtforms.fields import RadioField
from wtforms.validators import InputRequired
from wtforms.fields import DateField


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest

    class FormSubmissionsExportBase(DateRangeForm, ExportForm):
        pass
else:
    FormSubmissionsExportBase = merge_forms(DateRangeForm, ExportForm)


class FormSubmissionsExport(FormSubmissionsExportBase):

    if TYPE_CHECKING:
        request: OrgRequest

    selection = RadioField(
        label=_('Selection'),
        default='date',
        choices=[
            ('date', _('By date')),
            ('window', _('By registration window'))
        ]
    )

    registration_window = MultiCheckboxField(
        label=_('Registration Window'),
        choices=None,
        depends_on=('selection', 'window')
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        depends_on=('selection', 'date')
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()],
        depends_on=('selection', 'date')
    )

    def on_request(self) -> None:
        if self.registration_window.choices is None:
            self.load_registration_windows()  # type:ignore[unreachable]

            if not self.registration_window.choices:
                self.hide(self.selection)

    def load_registration_windows(self) -> None:
        # FIXME: circular import - a layout class just to get a date format?
        from onegov.org.layout import DefaultLayout

        layout = DefaultLayout(self.model, self.request)

        windows = sorted(
            self.model.registration_windows,
            key=attrgetter('start')
        )

        self.registration_window.choices = [
            (window.id.hex, layout.format_date_range(window.start, window.end))
            for window in windows
        ]
