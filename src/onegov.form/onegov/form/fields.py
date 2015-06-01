import base64
import magic
import zlib

from wtforms import FileField, StringField, SelectMultipleField, widgets
from wtforms.widgets import html5 as html5_widgets


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class TimeField(StringField):
    widget = html5_widgets.TimeInput


class UploadField(FileField):
    """ A custom file field that turns the uploaded file into a compressed
    base64 string together with the filename, size and mimetype.

    """

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = self.process_fieldstorage(valuelist[0])
        else:
            self.data = {}

    def process_fieldstorage(self, fs):
        file_data = fs.file.read()

        mimetype_by_introspection = magic.from_buffer(file_data, mime=True)
        mimetype_by_introspection = mimetype_by_introspection.decode('utf-8')

        compressed_data = zlib.compress(file_data)

        return {
            'data': base64.b64encode(compressed_data).decode('ascii'),
            'filename': fs.filename,
            'mimetype': mimetype_by_introspection,
            'size': len(file_data)
        }
