from onegov.form import Form
from onegov.gis import CoordinatesField
from onegov.translator_directory import _


class LocationSettingsForm(Form):

    coordinates = CoordinatesField(
        label=_("Home Location"),
        render_kw={'data-map-type': 'marker', 'data-undraggable': 1},
    )

    def apply_coordinates(self, app):
        app.coordinates = self.coordinates.data

    def process_coordinates(self, app):
        self.coordinates.data = app.coordinates
