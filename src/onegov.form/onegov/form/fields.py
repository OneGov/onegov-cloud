from onegov.core.html import sanitize_html
from onegov.core.utils import binary_to_dictionary
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
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

    @property
    def is_image(self):
        return self.data and\
            self.data.get('mimetype') in IMAGE_MIME_TYPES_AND_SVG

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
        self.file = getattr(fs, 'file', getattr(fs, 'stream', None))
        self.filename = getattr(fs, 'filename', None)

        if not self.file:
            return {}

        self.file.seek(0)

        try:
            return binary_to_dictionary(self.file.read(), self.filename)
        finally:
            self.file.seek(0)


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
