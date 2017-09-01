import json

from base64 import b64decode, b64encode
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
        text = json.dumps(self.data.as_dict())
        text = b64encode(text.encode('ascii'))
        text = text.decode('ascii')

        return text

    def process_data(self, value):
        if isinstance(value, Coordinates):
            self.data = value
        else:
            self.data = value and Coordinates(**value) or Coordinates()

    def populate_obj(self, obj, name):
        setattr(obj, name, self.data and self.data.as_dict() or None)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            text = b64decode(valuelist[0])
            text = text.decode('ascii')
            self.data = Coordinates(**json.loads(text))
        else:
            self.data = Coordinates()
