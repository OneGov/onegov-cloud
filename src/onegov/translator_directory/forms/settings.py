from onegov.form import Form
from onegov.gis import CoordinatesField
from onegov.translator_directory import _
from wtforms.fields import URLField
from wtforms.validators import Optional
from wtforms.validators import URL


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

    declaration_link = URLField(
        label=_("Link to declaration of authorization"),
        fieldset=_("Accreditation"),
        validators=[URL(), Optional()]
    )

    def update_model(self, app):
        app.org.meta = app.org.meta or {}
        if self.coordinates.data:
            app.coordinates = self.coordinates.data
        app.org.meta['declaration_link'] = \
            self.declaration_link.data

    def apply_model(self, app):
        self.coordinates.data = app.coordinates
        self.declaration_link.data = app.org.meta.get(
            'declaration_link', ''
        )
