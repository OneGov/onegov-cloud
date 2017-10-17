import os

from onegov.core.html import sanitize_html
from onegov.core.utils import binary_to_dictionary
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


class RawUploadField(FileField):
    """ A custom file field that that supports keeping/deleting and replacing
    files through the use of a custom widget.

    """

    widget = UploadWidget()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fieldstorage = None

    def process_formdata(self, valuelist):
        # the upload widget optionally includes an action with the request,
        # indicating if the existing file should be replaced, kept or deleted
        if valuelist:
            if len(valuelist) == 2:
                action, self.fieldstorage = valuelist
            else:
                action = 'new'
                self.fieldstorage = valuelist[0]

            self.data = getattr(self, '{}_file'.format(action))()
        else:
            self.data = None

    @property
    def file(self):
        return getattr(self.fieldstorage, 'file', None) or\
            getattr(self.fieldstorage, 'stream', None)

    @property
    def filename(self):
        return getattr(self.fieldstorage, 'filename', None)

    @property
    def filesize(self):
        if not self.file:
            return 0

        self.file.seek(0, os.SEEK_END)
        return self.file.tell()

    def new_file(self):
        raise NotImplementedError

    def delete_file(self):
        raise NotImplementedError

    def keep_file(self):
        raise NotImplementedError


class UploadField(RawUploadField):
    """ Turns the uploaded file into a json structure containing the
    data as a compressed base64 string.

    """

    @property
    def filename(self):
        return super().filename or self.data and self.data.get('filename')

    @property
    def filesize(self):
        return super().filesize or self.data and self.data.get('size')

    def new_file(self):
        if not self.file:
            return {}

        self.file.seek(0)
        return binary_to_dictionary(self.file.read(), self.filename)

    def delete_file(self):
        return {}

    def keep_file(self):
        return None


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
