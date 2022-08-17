from onegov.form import Form
from onegov.gis import CoordinatesField
from onegov.translator_directory import _

ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
}


class TranslatorDirectorySettingsForm(Form):

    coordinates = CoordinatesField(
        fieldset=_("Home Location"),
        render_kw={'data-map-type': 'marker', 'data-undraggable': 1},
    )

    def update_model(self, app):
        if self.coordinates.data:
            app.coordinates = self.coordinates.data

    def apply_model(self, app):
        self.coordinates.data = app.coordinates
