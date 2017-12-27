from onegov.form.extensions import FormExtension
from onegov.gis import CoordinatesField
from onegov.org import _
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class CoordinatesFormExtension(FormExtension, name='coordinates'):

    def create(self):
        class CoordinatesForm(self.form_class):
            coordinates = CoordinatesField(
                label=_("Coordinates"),
                description=_(
                    "The marker can be moved by dragging it with the mouse"
                ),
                fieldset=_("Map"),
                render_kw={'data-map-type': 'marker'}
            )

        return CoordinatesForm


class SubmitterFormExtension(FormExtension, name='submitter'):

    def create(self):
        class SubmitterForm(self.form_class):
            submitter = EmailField(
                label=_("E-Mail"),
                fieldset=_("Submitter"),
                validators=[DataRequired()]
            )

        return SubmitterForm
