import base64
import magic
import zlib

from mimetypes import types_map
from onegov.form.errors import InvalidMimeType
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

    It also checks that the mimetype is found in a whitelist and makes sure
    that the mimetype the file claims to be(by extension) is equal to the
    mimetype we find by inspecting the file using magic.

    This means that for now files need an extension...

    """

    whitelist = {
        'application/excel',
        'application/vnd.ms-excel',
        'application/msword',
        'application/pdf',
        'application/zip',
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/x-ms-bmp',
        'text/plain',
    }

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = self.process_fieldstorage(valuelist[0])
        else:
            self.data = {}

    def process_fieldstorage(self, fs):
        file_ext = '.' + fs.filename.split('.')[-1]
        file_data = fs.file.read()

        mimetype_by_extension = types_map.get(file_ext, '0xdeadbeef')
        mimetype_by_introspection = magic.from_buffer(file_data, mime=True)
        mimetype_by_introspection = mimetype_by_introspection.decode('utf-8')

        if mimetype_by_extension != mimetype_by_introspection:
            raise InvalidMimeType()

        if mimetype_by_introspection not in self.whitelist:
            raise InvalidMimeType()

        compressed_data = zlib.compress(file_data)

        return {
            'data': base64.b64encode(compressed_data).decode('ascii'),
            'filename': fs.filename,
            'mimetype': mimetype_by_introspection,
            'size': len(file_data)
        }
