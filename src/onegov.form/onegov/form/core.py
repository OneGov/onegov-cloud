import inspect
import weakref

from collections import OrderedDict
from itertools import groupby
from onegov.form import utils
from operator import itemgetter
from wtforms import Form as BaseForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, DataRequired, Optional
from wtforms_components import If, Chain


class Form(BaseForm):
    """ Extends wtforms.Form with useful methods and integrations needed in
    OneGov applications.

    Fieldsets
    ---------

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

    Dependencies
    ------------

    This form also supports dependencies. So field b may depend on field a, if
    field a has a certain value, field b is shown on the form (with some
    javascript) and its validators are actually executed. If field a does
    not have the required value, field b is hidden with javascript and its
    validators are not executed.

    The validators which are skipped are only the validators passed with the
    field, the validators on the field itself are still invoked (we can't
    skip them). However, only if the optional field is not empty. That is we
    prevent invalid values no matter what, but we allow for empty values if
    the dependent field does not have the required value.

    This sounds a lot more complicated than it is::

        class MyForm(Form):

            option = RadioField('Option', choices=[
                ('yes', 'Yes'),
                ('no', 'No'),
            ])
            only_if_no = StringField(
                label='Only Shown When No',
                validators=[InputRequired()],
                depends_on=('option', 'no')
            )

    """

    def __init__(self, *args, **kwargs):

        # preprocessors are generators which yield control to give the
        # constructor the chance to call the parent constructor. Their
        # purpose is to handle custom attributes passed to the fields,
        # removing them in the process (so wtforms doesn't trip up).
        preprocessors = [
            self.process_fieldset(),
            self.process_depends_on()
        ]

        for processor in preprocessors:
            next(processor)

        super().__init__(*args, **kwargs)

        for processor in preprocessors:
            next(processor, None)

    def process_fieldset(self):
        """ Processes the fieldset parameter on the fields, which puts
        fields into fieldsets.

        In the process the fields are altered so that wtforms recognizes them
        again (that is, attributes only known to us are removed).

        See :class:`Form` for more information.

        """

        self.fieldsets = []

        # consume the fieldset attribute of all unbound fields, as WTForms
        # doesn't know it -> move it to the field which is a *class* attribute
        # (so this only happens once per class)
        for field_id, field in self._unbound_fields:
            if not hasattr(field, 'fieldset'):
                field.fieldset = field.kwargs.pop('fieldset', None)

        fields_by_fieldset = [
            (field.fieldset, field_id)
            for field_id, field in self._unbound_fields
        ]

        # yield control to the constructor so it can call the parent
        yield

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

    def process_depends_on(self):
        """ Processes the depends_on parameter on the fields, which adds the
        ability to have fields depend on values of other fields.

        In the process the fields are altered so that wtforms recognizes them
        again (that is, attributes only known to us are removed).

        See :class:`Form` for more information.

        """

        for field_id, field in self._unbound_fields:

            if 'depends_on' not in field.kwargs:
                continue

            depends_on = field.kwargs.pop('depends_on')

            if not depends_on:
                continue

            field.depends_on = FieldDependency(*depends_on)

            if 'validators' in field.kwargs:
                field.kwargs['validators'] = (
                    If(
                        field.depends_on.fulfilled,
                        Chain(field.kwargs['validators'])
                    ),
                    If(
                        field.depends_on.unfulfilled,
                        Optional()
                    ),
                )

            field.kwargs['render_kw'] = field.kwargs.get('render_kw', {})
            field.kwargs['render_kw'].update(field.depends_on.html_data)

        yield

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

    def populate_obj(self, obj, exclude=None, include=None):
        """ A reimplementation of wtforms populate_obj function with the addage
        of optional include/exclude filters.

        If neither exclude nor include is passed, the function works like it
        does in wtforms. Otherwise fields are considered which are included
        but not excluded.

        """

        include = include or set(self._fields.keys())
        exclude = exclude or set()

        for name, field in self._fields.items():
            if name in include and name not in exclude:
                field.populate_obj(obj, name)


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

    Note: With wtforms 2.1 this is no longer necssary. Instead use the
    render_kw parameter of the field class. This function will be deprecated
    in a future release.

    """

    if inspect.isclass(widget):
        class Widget(widget):

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return super().__call__(*args, **render_options)

        return Widget()
    else:
        class Widget(widget.__class__):

            def __init__(self):
                self.__dict__.update(widget.__dict__)

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return widget.__call__(*args, **render_options)

        return Widget()


class FieldDependency(object):
    """ Defines a dependency to a field. The given field must have the given
    choice for this dependency to be fulfilled.

    """

    def __init__(self, field_id, choice):
        self.field_id = field_id
        self.choice = choice

    def fulfilled(self, form, field):
        return getattr(form, self.field_id).data == self.choice

    def unfulfilled(self, form, field):
        return not self.fulfilled(form, field)

    @property
    def html_data(self):
        return {'data-depends-on': '/'.join((self.field_id, self.choice))}


def merge_forms(*forms):
    """ Takes a list of forms and merges them.

    In doing so, a new class is created which inherits from all the forms in
    the default method resolution order. So the first class will override
    fields in the second class and so on.

    So this method is basically the same as:

        class Merged(*forms):
            pass

    With *one crucial difference*, the order of the fields is as follows:

    First, the fields from the first form are rendered, then the fields
    from the second form and so on. This is not the case if you merge the
    forms by simple class inheritance, as each form has it's own internal
    field order, which when merged leads to unexpected results.

    """

    class MergedForm(*forms):
        pass

    processed = set()
    fields_in_order = (
        name for cls in forms for name, field
        in utils.get_fields_from_class(cls)
    )

    for counter, name in enumerate(fields_in_order, start=1):
        if name in processed:
            continue

        getattr(MergedForm, name).creation_counter = counter
        processed.add(name)

    return MergedForm
