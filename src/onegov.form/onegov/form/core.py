import inspect
import weakref

from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.form import utils
from onegov.pay import Price
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

    Pricing
    -------

    Pricing is a way to attach prices to certain form fields. A total price
    is calcualted depending on the selections the user makes::

        class MyForm(Form):

            ticket_insurance = RadioField('Option', choices=[
                ('yes', 'Yes'),
                ('no', 'No')
            ], pricing={
                'yes': (10.0, 'CHF')
            })

            discount_code = TextField('Discount Code', pricing={
                'CAMPAIGN2017': (-5.0, 'CHF')
            })

    Note that the pricing has no implicit meaning. This is simply a way to
    attach prices and to get the total through the ``prices()`` and ``total()``
    calls. What you do with these prices is up to you.

    """

    def __init__(self, *args, **kwargs):

        # preprocessors are generators which yield control to give the
        # constructor the chance to call the parent constructor. Their
        # purpose is to handle custom attributes passed to the fields,
        # removing them in the process (so wtforms doesn't trip up).
        preprocessors = [
            self.process_fieldset(),
            self.process_depends_on(),
            self.process_pricing()
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

    def process_pricing(self):
        """ Processes the pricing parameter on the fields, which adds the
        ability to have fields associated with a price.

        See :class:`Form` for more information.

        """

        pricings = {}

        # move the pricing rule to the field class (happens once per class)
        for field_id, field in self._unbound_fields:
            if not hasattr(field, 'pricing'):
                field.pricing = field.kwargs.pop('pricing', None)

        # prepare the pricing rules
        for field_id, field in self._unbound_fields:
            if field.pricing:
                pricings[field_id] = Pricing(field.pricing)

        yield

        # attach the pricing rules to the field instances
        for field_id, pricing in pricings.items():
            self._fields[field_id].pricing = pricing

    def is_visible_through_dependencies(self, field_id):
        """ Returns true if the given field id has visible because all of
        it's parents are visible. A field is invisible if its dependency is
        not met.

        """

        unbound_field = getattr(self.__class__, field_id)
        depends_on = getattr(unbound_field, 'depends_on', None)

        if not depends_on:
            return True

        bound_field = getattr(self, field_id)

        if not depends_on.fulfilled(self, bound_field):
            return False

        return all(
            self.is_visible_through_dependencies(d['field_id'])
            for d in depends_on.dependencies
        )

    def prices(self):
        """ Returns the prices of all selected items depending on the
        formdata. """

        prices = []

        for field_id, field in self._fields.items():
            if not hasattr(field, 'pricing'):
                continue

            if not self.is_visible_through_dependencies(field_id):
                continue

            price = field.pricing.price(field)

            if price is not None:
                prices.append((field_id, price))

        currencies = set(price.currency for _, price in prices)
        assert len(currencies) <= 1, "Mixed currencies are not supported"

        return prices

    def total(self):
        """ Returns the total amount of all prices. """
        prices = self.prices()

        if not prices:
            return None

        return Price(
            sum(price.amount for field_id, price in prices),
            prices[0][1].currency
        )

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

    def process(self, *args, **kwargs):
        """ Calls :meth:`process_obj` if ``process()`` was called with
        the ``obj`` keyword argument.

        This saves an extra check in many cases where we want to extend the
        process function, but only *if* an obj has been provided.

        """
        super().process(*args, **kwargs)

        if 'obj' in kwargs:
            self.process_obj(kwargs.get('obj'))

    def process_obj(self, obj):
        """ Called by :meth:`process` if an object was passed.

        Do *not* use this function directly. To process an object, you should
        call ``form.process(obj=obj)`` instead.

        """
        pass

    def delete_field(self, fieldname):
        """ Removes the given field from the form and all the fieldsets. """

        def fieldsets_without_field():
            for fieldset in self.fieldsets:
                if fieldname in fieldset.fields:
                    del fieldset.fields[fieldname]

                if fieldset.fields:
                    yield fieldset

        self.fieldsets = list(fieldsets_without_field())

        del self[fieldname]

    def validate(self):
        """ Adds support for 'ensurances' to the form. An ensurance is a
        method which is called during validation when all the fields have
        been populated. Therefore it is a good place to validate against
        multiple fields.

        All methods which start with 'ensure_' are ensurances. If and only if
        an ensurance returns False it is considered to have failed. In this
        case the validate method returns False as well. If None or '' or
        any other falsy value is returned, no error is assumed! This avoids
        having to return an extra True at the end of each ensurance.

        When one ensurance fails, the others are still run. Also, there's no
        error display mechanism. Showing an error is left to the ensurance
        itself. It can do so by adding messages to the various error lists
        of the form or by showing an alert through the request.

        """
        result = super().validate()

        for ensurance in self.ensurances:
            if ensurance() is False:
                result = False

        return result

    @property
    def ensurances(self):
        """ Returns the ensurances that need to be checked when validating.

        This property may be overridden if only a subset of all ensurances
        should actually be enforced.

        """

        # inspect.getmembers is no good here as it triggers the properties
        for name in dir(self):
            if name.startswith('ensure_'):

                if isinstance(getattr(type(self), name), property):
                    continue

                member = getattr(self, name)

                if callable(member):
                    yield member


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
    """ Defines a dependency to a field. The given field(s) must have the given
    choice for this dependency to be fulfilled.

    It's possible to depend on NOT the given value by preceeding it with a '!':

        FieldDependency('field_1', '!choice_1')

    To depend on more than one field, add the field_id's and choices to the
    constructor:

        FieldDependency('field_1', 'choice_1')
        FieldDependency('field_1', 'choice_1', 'field_2', 'choice_2')

    """

    def __init__(self, *kwargs):
        assert len(kwargs) and not len(kwargs) % 2

        self.dependencies = []
        for index in range(len(kwargs) // 2):
            choice = kwargs[2 * index + 1]
            invert = choice.startswith('!')
            self.dependencies.append({
                'field_id': kwargs[2 * index],
                'raw_choice': choice,
                'invert': invert,
                'choice': choice[1:] if invert else choice,
            })

    def fulfilled(self, form, field):
        result = True
        for dependency in self.dependencies:
            data = getattr(form, dependency['field_id']).data
            choice = dependency['choice']
            invert = dependency['invert']
            result = result and ((data == choice) ^ invert)
        return result

    def unfulfilled(self, form, field):
        return not self.fulfilled(form, field)

    @property
    def field_id(self):
        return self.dependencies[0]['field_id']

    @property
    def html_data(self):
        value = ';'.join((
            '/'.join((dep['field_id'], dep['raw_choice']))
            for dep in self.dependencies
        ))
        return {'data-depends-on': value}


class Pricing(object):
    """ Defines pricing on a field, returning the correct price for the field
    depending on its rule.

    """

    def __init__(self, rules):
        self.rules = {
            rule: Price(Decimal(value), currency)
            for rule, (value, currency) in rules.items()
        }

    def price(self, field):
        if isinstance(field.data, list):
            total = None

            for value in field.data:
                price = self.rules.get(value, None)

                if price is not None:
                    total = (total or Decimal(0)) + price.amount
                    currency = price.currency

            if total is None:
                return None
            else:
                return Price(total, currency)

        return self.rules.get(field.data, None)


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

    fields_in_order = (
        name for cls in forms for name, field
        in utils.get_fields_from_class(cls)
    )

    return enforce_order(MergedForm, fields_in_order)


def enforce_order(form_class, fields_in_order):
    """ Takes a list of fields used in a form_class and enforces the
    order of those fields.

    If not all fields in the form are given, the resulting order is undefined.

    """

    # XXX to make sure the field order of the existing class remains
    # unchanged, we need to instantiate the class once (wtforms seems
    # to do some housekeeping somehwere)
    form_class()

    class EnforcedOrderForm(form_class):
        pass

    processed = set()

    for counter, name in enumerate(fields_in_order, start=1):
        if name in processed:
            continue

        getattr(EnforcedOrderForm, name).creation_counter = counter
        processed.add(name)

    return EnforcedOrderForm


def move_fields(form_class, fields, after):
    """ Reorders the given fields (given by name) by inserting them directly
    after the given field.

    If ``after`` is None, the fields are moved to the end.

    """

    fields_in_order = []

    for name, _ in utils.get_fields_from_class(form_class):
        if name in fields:
            continue

        fields_in_order.append(name)

        if name == after:
            fields_in_order.extend(fields)

    if after is None:
        fields_in_order.extend(fields)

    return enforce_order(form_class, fields_in_order)
