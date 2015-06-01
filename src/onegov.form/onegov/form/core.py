import base64
import inspect
import magic
import weakref
import zlib

from collections import OrderedDict
from itertools import groupby
from onegov.form.errors import InvalidMimeType
from operator import itemgetter
from mimetypes import types_map
from wtforms import FileField
from wtforms import Form as BaseForm


default_whitelist = {
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


class Form(BaseForm):
    """ Extends wtforms.Form with useful methods and integrations needed in
    OneGov applications.

    This form supports fieldsets (which WTForms doesn't recognize). To put
    fields into a fieldset, add a fieldset attribute to the field during
    class definition::

        class MyForm(Form):
            first_name = StringField('First Name', fieldset='Name')
            last_name = StringField('Last Name', fieldset='Name')
            comment = StringField('Comment')

    A form created like this will have two fieldsets, one visible fieldset
    with the legend set to 'Name' and one invisible fieldset containing
    'comment'.

    Fieldsets with the same name are *not* automatically grouped together.
    Instead, fields are taken in the order they are defined and put into the
    same fieldset, if the previous fieldset has the same name.

    That is to say, in this example, we get three fieldsets::

        class MyForm(Form):
            a = StringField('A', fieldset='1')
            b = StringField('B', fieldset='2')
            c = StringField('C', fieldset='1')

    The first fieldset has the label '1' and it contains 'a'. The second
    fieldset has the label '2' and it contains 'b'. The third fieldset has
    the label '3' and it contains 'c'.

    This ensures that all fields are in either a visible or an invisible
    fieldset (see :meth:`Fieldset.is_visible`).

    """

    def __init__(self, *args, **kwargs):

        # consume the fieldset attribute of all unbound fields, as WTForms
        # doesn't know it
        fields_by_fieldset = [
            (field.kwargs.pop('fieldset', None), field_id)
            for field_id, field in self._unbound_fields
        ]

        super(Form, self).__init__(*args, **kwargs)

        # use the consumed fieldset attribute to build fieldsets
        self.fieldsets = []

        # wtforms' constructor might add more fields not available as
        # unbound fields (like the csrf token)
        if len(self._fields) != len(self._unbound_fields):
            processed = set(f[1] for f in fields_by_fieldset)
            extra = (
                f[1] for f in self._fields.items() if f[0] not in processed
            )
            self.fieldsets.append(Fieldset(None, fields=extra))

        for label, fields in groupby(fields_by_fieldset, key=itemgetter(0)):
            self.fieldsets.append(Fieldset(
                label=label,
                fields=(self._fields[f[1]] for f in fields)
            ))

    def submitted(self, request, whitelist=default_whitelist):
        """ Returns true if the given request is a successful post request. """
        valid = request.POST and self.validate()

        if not valid:
            return False

        # load the files, making sure their mime type is on a whitelist and
        # that their mimetype matches the extension they have
        #
        # access the files through self._files after that
        for field in self._fields.values():
            if isinstance(field, FileField):
                field.data = self.load_file(request, field)

        return True

    def load_file(self, request, field, whitelist=default_whitelist):
        """ Loads the given input field from the request, making sure it's
        mimetype matches the extension and is found in the mimetype whitelist.

        """

        file_ext = '.' + field.data.filename.split('.')[-1]
        file_data = request.POST[field.id].file.read()

        mimetype_by_extension = types_map.get(file_ext, '0xdeadbeef')
        mimetype_by_introspection = magic.from_buffer(file_data, mime=True)
        mimetype_by_introspection = mimetype_by_introspection.decode('utf-8')

        if mimetype_by_extension != mimetype_by_introspection:
            raise InvalidMimeType()

        if mimetype_by_introspection not in whitelist:
            raise InvalidMimeType()

        compressed_data = zlib.compress(file_data)

        return {
            'data': base64.b64encode(compressed_data).decode('ascii'),
            'filename': field.data.filename,
            'mimetype': mimetype_by_introspection,
            'size': len(file_data)
        }


class Fieldset(object):
    """ Defines a fieldset with a list of fields. """

    def __init__(self, label, fields):
        """ Initializes the Fieldset.

        :label: Label of the fieldset (None if it's an invisible fieldset)
        :fields: Iterator of bound fields. Fieldset creates a list of weak
        references to these fields, as they are defined elsewhere and should
        not be kept in memory just because a Fieldset references them.

        """
        self.label = label
        self.fields = OrderedDict((f.id, weakref.proxy(f)) for f in fields)

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, key):
        return self.fields[key]

    @property
    def is_visible(self):
        return self.label is not None


def with_options(widget, **render_options):
    """ Takes a widget class or instance and returns a child-instance of the
    widget class, with the given options set on the render call.

    This makes it easy to use existing WTForms widgets with custom render
    options:

    field = StringField(widget=with_options(TextArea, class_="markdown"))

    """

    if inspect.isclass(widget):
        class Widget(widget):

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return super(Widget, self).__call__(*args, **render_options)

        return Widget()
    else:
        class Widget(widget.__class__):

            def __init__(self):
                self.__dict__.update(widget.__dict__)

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return widget.__call__(*args, **render_options)

        return Widget()
