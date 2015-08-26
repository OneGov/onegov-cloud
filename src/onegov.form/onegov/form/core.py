import inspect
import weakref

from collections import OrderedDict
from itertools import groupby
from operator import itemgetter
from wtforms import Form as BaseForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, DataRequired


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

    def submitted(self, request):
        """ Returns true if the given request is a successful post request. """
        return request.POST and self.validate()

    def ignore_csrf_error(self):
        """ Removes the csrf error from the form if found, after validation.

        Use this only if you know what you are doing (really, never).

        """
        if self.meta.csrf_field_name in self.errors:
            del self.errors[self.meta.csrf_field_name]
            self.csrf_token.errors = []

    @property
    def has_required_email_field(self):
        """ Returns True if the form has a required e-mail field. """
        matches = self.match_fields(
            include_classes=(EmailField, ),
            required=True,
            limit=1
        )

        return matches and True or False

    def match_fields(self, include_classes=None, exclude_classes=None,
                     required=None, limit=None):
        """ Returns field ids matching the given search criteria.

        :include_classes:
            A list of field classes which should be included.

        :excluded_classes:
            A list of field classes which should be excluded.

        :required:
            True if required fields only, False if no required fields.

        :limit:
            If > 0, limits the number of returned elements.

        All parameters may be set to None disable matching it to anything.

        """

        matches = []

        for field_id, field in self._fields.items():
            if include_classes:
                for cls in include_classes:
                    if isinstance(field, cls):
                        break
                else:
                    continue

            if exclude_classes:
                for cls in exclude_classes:
                    if not isinstance(field, cls):
                        break
                else:
                    continue

            if required is True and not self.is_required(field_id):
                continue

            if required is False and self.is_required(field_id):
                continue

            matches.append(field_id)

            if limit and len(matches) == limit:
                break

        return matches

    def is_required(self, field_id):
        """ Returns true if the given field_id is required. """

        for validator in self._fields[field_id].validators:
            if isinstance(validator, (InputRequired, DataRequired)):
                return True
        return False

    def get_useful_data(self, exclude={'csrf_token'}):
        """ Returns the form data in a dictionary, by default excluding data
        that should not be stored in the db backend.

        """

        return {k: v for k, v in self.data.items() if k not in exclude}


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

    @property
    def non_empty_fields(self):
        """ Returns only the fields which are not empty. """
        return OrderedDict(
            (id, field) for id, field in self.fields.items() if field.data)


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
