import base64
import gzip
import magic

from io import BytesIO
from onegov.core.html import sanitize_html
from onegov.form.widgets import MultiCheckboxWidget
from onegov.form.widgets import OrderedMultiCheckboxWidget
from onegov.form.widgets import UploadWidget
from wtforms import FileField, SelectMultipleField, TextAreaField, widgets


class MultiCheckboxField(SelectMultipleField):

    widget = MultiCheckboxWidget()
    contains_labels = True

    def __init__(self, *args, **kwargs):
        kwargs['option_widget'] = widgets.CheckboxInput()
        super().__init__(*args, **kwargs)


class OrderedMultiCheckboxField(MultiCheckboxField):
    widget = OrderedMultiCheckboxWidget()


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


class HtmlField(TextAreaField):
    """ A textfield with html with integrated sanitation. """

    def __init__(self, *args, **kwargs):
        self.form = kwargs.get('_form')

        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editor'

        super().__init__(*args, **kwargs)

    def pre_validate(self, form):
        self.data = sanitize_html(self.data)
