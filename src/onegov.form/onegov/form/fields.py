import base64
import gzip
import magic

from io import BytesIO
from onegov.form.widgets import (
    CoordinateWidget,
    MultiCheckboxWidget,
    UploadWidget
)
from wtforms import FileField, SelectMultipleField, StringField, widgets


class MultiCheckboxField(SelectMultipleField):

    widget = MultiCheckboxWidget()
    contains_labels = True

    def __init__(self, *args, **kwargs):
        kwargs['option_widget'] = widgets.CheckboxInput()
        super().__init__(*args, **kwargs)


class CoordinateField(StringField):
    """ Represents a single coordinate in the form lat/lon.

    In the browser and during transit the coordinate is stored as a string
    on a simple input field. For example::

        8.30576869173879/47.05183585

    For verification: This coordinate points to the Seantis office in Lucerne.

    For convenience, the coordinate is accessible with the :class:`Coordinate`
    class however, which offers named attributes and float values.

    """

    widget = CoordinateWidget()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = getattr(self, 'data', Coordinate())

    def _value(self):
        return self.data.as_text()

    def process_formdata(self, valuelist):
        self.data = Coordinate.from_text(valuelist and valuelist[0] or None)


class Coordinate(object):
    """ Represents a single coordinate as string internally and as float
    through a public interface. Used by :class: `CoordinateField`.

    """

    def __init__(self, lat=None, lon=None):
        self.lat = lat
        self.lon = lon

    def __bool__(self):
        return (self.lat and self.lon) and True or False

    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @lat.setter
    def lat(self, value):
        self._lat = float(value) if value else None

    @lon.setter
    def lon(self, value):
        self._lon = float(value) if value else None

    @classmethod
    def from_text(cls, text):
        lat, lon = [float(p) for p in text.split('/')]
        return cls(lat=lat, lon=lon)

    def as_text(self):
        if self:
            return '/'.join(str(p) for p in (self.lat, self.lon))
        else:
            return ''


class UploadField(FileField):
    """ A custom file field that turns the uploaded file into a compressed
    base64 string together with the filename, size and mimetype.

    """

    widget = UploadWidget()

    def process_formdata(self, valuelist):
        # the upload widget optionally includes an action with the request,
        # indicating if the existing file should be replaced, kept or deleted
        if valuelist:
            if len(valuelist) == 2:
                action, fieldstorage = valuelist
            else:
                action = 'replace'
                fieldstorage = valuelist[0]

            if action == 'replace':
                self.data = self.process_fieldstorage(fieldstorage)
            elif action == 'delete':
                self.data = {}
            elif action == 'keep':
                pass
            else:
                raise NotImplementedError()
        else:
            self.data = {}

    def process_fieldstorage(self, fs):

        # support webob and werkzeug multidicts
        fp = getattr(fs, 'file', getattr(fs, 'stream', None))

        if fp is None:
            return {}
        else:
            fp.seek(0)

        file_data = fp.read()

        mimetype_by_introspection = magic.from_buffer(file_data, mime=True)
        mimetype_by_introspection = mimetype_by_introspection.decode('utf-8')

        compressed_data = BytesIO()
        with gzip.GzipFile(fileobj=compressed_data, mode="wb") as f:
            f.write(file_data)

        return {
            'data': base64.b64encode(
                compressed_data.getvalue()).decode('ascii'),
            'filename': fs.filename,
            'mimetype': mimetype_by_introspection,
            'size': len(file_data)
        }
