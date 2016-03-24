from onegov.gis.forms.widgets import MapPointWidget
from onegov.gis.models import Point
from wtforms.fields import StringField


class MapPointField(StringField):
    """ Represents a single point on a geograpbhic coordinate system
    in the form lat/lon as a textfield.

    In the browser and during transit the point is stored as a string
    on a simple input field. For example::

        8.30576869173879/47.05183585

    For verification: This points to the Seantis office in Lucerne.

    For convenience, the point is accessible with the :class:`Point`
    class, which offers named attributes and float values.

    """

    widget = MapPointWidget()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = getattr(self, 'data', Point())

    def _value(self):
        return self.data.as_text()

    def process_data(self, value):
        self.data = value or Point()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = Point.from_text(valuelist and valuelist[0])
        else:
            self.data = Point()
