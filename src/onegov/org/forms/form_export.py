from onegov.org import _
from onegov.org.forms.generic import DateRangeForm, ExportForm
from onegov.form import merge_forms
from onegov.form.fields import MultiCheckboxField
from wtforms import RadioField
from wtforms import validators
from wtforms.fields.html5 import DateField


class FormSubmissionsExport(merge_forms(DateRangeForm, ExportForm)):

    selection = RadioField(
        label=_("Selection"),
        default='date',
        choices=[
            ('date', _("By date")),
            ('window', _("By registration window"))
        ]
    )

    registration_window = MultiCheckboxField(
        label=_("Registration Window"),
        choices=None,
        depends_on=('selection', 'window')
    )

    start = DateField(
        label=_("Start"),
        validators=[validators.InputRequired()],
        depends_on=('selection', 'date')
    )

    end = DateField(
        label=_("End"),
        validators=[validators.InputRequired()],
        depends_on=('selection', 'date')
    )

    def on_request(self):
        if self.registration_window.choices is None:
            self.load_registration_windows()

            if not self.registration_window.choices:
                self.hide(self.selection)

    def load_registration_windows(self):
        # XXX circular import - also, a layout class just to get a date format?
        from onegov.org.layout import DefaultLayout

        layout = DefaultLayout(self.model, self.request)

        def key(window):
            return window.id.hex

        def title(window):
            return layout.format_date_range(window.start, window.end)

        def choice(window):
            return key(window), title(window)

        windows = self.model.registration_windows
        windows.sort(key=lambda r: r.start)

        self.registration_window.choices = tuple(choice(w) for w in windows)
