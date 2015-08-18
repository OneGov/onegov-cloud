import base64
import gzip
import magic

from onegov.core.compat import BytesIO
from onegov.form.widgets import MultiCheckboxWidget, UploadWidget
from wtforms import FileField, SelectMultipleField, widgets


class MultiCheckboxField(SelectMultipleField):

    widget = MultiCheckboxWidget()

    def __init__(self, *args, **kwargs):
        kwargs['option_widget'] = widgets.CheckboxInput()
        super(MultiCheckboxField, self).__init__(*args, **kwargs)


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
