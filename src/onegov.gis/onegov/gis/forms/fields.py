from base64 import b64decode, b64encode
from onegov.core.custom import json
from onegov.form.display import registry, BaseRenderer
from onegov.gis.forms.widgets import CoordinatesWidget
from onegov.gis.models import Coordinates
from wtforms.fields import StringField


class CoordinatesField(StringField):
    """ Represents a single pair of coordinates with optional zoom and
    marker icon/color selection.

    In the browser and during transit the point is stored as a base64 encoded
    json string on a simple input field. For example::

        eydsYXQnOiA4LjMwNTc2ODY5MTczODc5LCAnbG.. (and so on)

        =>

        {'lon': 8.30576869173879, 'lat': 47.05183585, 'zoom': 10}

    For verification: This points to the Seantis office in Lucerne.

    For convenience, the coordinates are accessible with the
    :class:`onegov.gis.models.coordinates.Coordinates` class when 'data' is
    used.

    Note that this field doesn't work with the ``InputRequired`` validator.
    Instead the ``DataRequired`` validator has to be chosen.

    """

    widget = CoordinatesWidget()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = getattr(self, 'data', Coordinates())

    def _value(self):
        text = json.dumps(self.data) or '{}'
        text = b64encode(text.encode('ascii'))
        text = text.decode('ascii')

        return text

    def process_data(self, value):
        if isinstance(value, dict):
            self.data = Coordinates(**value)
        else:
            self.data = value

    def populate_obj(self, obj, name):
        setattr(obj, name, self.data)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            text = b64decode(valuelist[0])
            text = text.decode('ascii')
            self.data = json.loads(text)
        else:
            self.data = Coordinates()

        # if the data we receive doesn't result in a coordinates value
        # for some reason, we create one
        if not isinstance(self.data, Coordinates):
            self.data = Coordinates()


@registry.register_for('CoordinatesField')
class CoordinatesFieldRenderer(BaseRenderer):
    def __call__(self, field):
        return """
            <div class="marker-map"
                 data-map-type="thumbnail"
                 data-lat="{lat}"
                 data-lon="{lon}"
                 data-zoom="{zoom}"></div>
        """.format(
            lat=field.data.lat,
            lon=field.data.lon,
            zoom=field.data.zoom
        )
