from __future__ import annotations

import weakref

from collections import OrderedDict
from decimal import Decimal
from itertools import chain, groupby
from markupsafe import Markup
from onegov.core.markdown import render_untrusted_markdown as render_md
from onegov.form import utils
from onegov.form.display import render_field
from onegov.form.fields import FIELDS_NO_RENDERED_PLACEHOLDER
from onegov.form.fields import HoneyPotField
from onegov.form.utils import get_fields_from_class
from onegov.form.validators import If, StrictOptional
from onegov.pay import InvoiceDiscountMeta, InvoiceItemMeta, Price
from operator import itemgetter
from wtforms import Form as BaseForm
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, DataRequired


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import (
        Callable, Collection, Iterable, Iterator, Mapping, Sequence)
    from onegov.core.request import CoreRequest
    from onegov.form.types import PricingRules
    from typing import TypedDict, Self
    from weakref import CallableProxyType
    from webob.multidict import MultiDict
    from wtforms import Field
    from wtforms.meta import _MultiDictLike

    class DependencyDict(TypedDict):
        field_id: str
        raw_choice: object
        invert: bool
        choice: object

_FormT = TypeVar('_FormT', bound='Form')


class Form(BaseForm):
    """ Extends wtforms.Form with useful methods and integrations needed in
    OneGov applications.

    **Fieldsets**

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

    **Dependencies**

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

    **Pricing**

    Pricing is a way to attach prices to certain form fields. A total price
    is calcualted depending on the selections the user makes::

        class MyForm(Form):

            ticket_insurance = RadioField('Option', choices=[
                ('yes', 'Yes'),
                ('no', 'No')
            ], pricing={
                'yes': (10.0, 'CHF')
            })

            stamps = IntegerRangeField(
            'No. Stamps',
            range=range(0, 30),
            pricing={range(0, 30): (1.00, 'CHF')}
        )

            delivery = RadioField('Delivery', choices=[
                ('pick_up', 'Pick up'),
                ('post', 'Post')
            ], pricing={
                'post': (5.0, 'CHF', True)
            })

            discount_code = StringField('Discount Code', pricing={
                'CAMPAIGN2017': (-5.0, 'CHF')
            })

    Note that the pricing has no implicit meaning. This is simply a way to
    attach prices and to get the total through the ``prices()`` and ``total()``
    calls. What you do with these prices is up to you.

    Pricing can optionally take a third boolean value indicating that this
    option will make credit card payments mandatory.

    """

    fieldsets: list[Fieldset]
    hidden_fields: set[str]

    if TYPE_CHECKING:
        # FIXME: These get set by the request, we should probably move them to
        #        meta, since that is where data like that is supposed to live
        #        but it'll be a pain to find everywhere we access request
        #        through anything other than meta.
        request: CoreRequest
        model: Any

        # NOTE: While action isn't guaranteed to be set, it almost always will
        #       be the way we use forms, see `onegov.core.directives` or more
        #       specifically `wrap_with_generic_form_handler`.
        action: str

    def __init__(
        self,
        formdata: MultiDict[str, Any] | None = None,
        obj: object | None = None,
        prefix: str = '',
        data: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        *,
        extra_filters: Mapping[str, Sequence[Any]] | None = None,
        **kwargs: Any
    ):

        # preprocessors are generators which yield control to give the
        # constructor the chance to call the parent constructor. Their
        # purpose is to handle custom attributes passed to the fields,
        # removing them in the process (so wtforms doesn't trip up).
        preprocessors = [
            self.process_fieldset(),
            self.process_depends_on(),
            self.process_pricing(),
            self.process_discount(),
        ]

        for processor in preprocessors:
            next(processor)

        super().__init__(
            formdata=formdata,
            obj=obj,
            prefix=prefix,
            data=data,
            meta=meta,
            extra_filters=extra_filters,
            **kwargs
        )

        for processor in preprocessors:
            next(processor, None)

        self.hidden_fields = set()

    @classmethod
    def clone(cls) -> type[Self]:
        """ Creates an independent copy of the form class.

        The fields of the so called class may be manipulated without affecting
        the original class.

        """

        class ClonedForm(cls):  # type:ignore
            pass

        for key, unbound_field in get_fields_from_class(cls):
            setattr(ClonedForm, key, unbound_field.field_class(
                *unbound_field.args,
                **unbound_field.kwargs
            ))

        return ClonedForm

    def process_fieldset(self) -> Iterator[None]:
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
            processed = {field_id for _, field_id in fields_by_fieldset}
            extra = (
                field
                for field_id, field in self._fields.items()
                if field_id not in processed
            )
            self.fieldsets.append(Fieldset(None, fields=extra))

        for label, fields in groupby(fields_by_fieldset, key=itemgetter(0)):
            self.fieldsets.append(Fieldset(
                label=label,
                fields=(self._fields[field_id] for _, field_id in fields)
            ))

    def process_depends_on(self) -> Iterator[None]:
        """ Processes the depends_on parameter on the fields, which adds the
        ability to have fields depend on values of other fields.

        Supported are dependencies to boolean fields and choices. Search
        the source code for depends_on for plenty of examples.

        For checkboxes, note that the value is 'y' (string) or '!y' for
        the inverse.

        In the process the fields are altered so that wtforms recognizes them
        again (that is, attributes only known to us are removed).

        See :class:`Form` for more information.

        """

        for field_id, field in self._unbound_fields:

            depends_on = field.kwargs.pop('depends_on', None)

            if not depends_on:
                continue

            field.depends_on = FieldDependency(*depends_on)

            if validators := field.kwargs.get('validators', None):

                # mirror the field flags of the first existing validator to the
                # field flags of the wrapper, to carry over things like the
                # 'required' flag
                field_flags = getattr(validators[0], 'field_flags', None)

                field.kwargs['validators'] = (
                    If(
                        field.depends_on.fulfilled,
                        *validators
                    ),
                    If(
                        field.depends_on.unfulfilled,
                        StrictOptional()
                    ),
                )

                if field_flags:
                    field.kwargs['validators'][0].field_flags = field_flags

            field.kwargs.setdefault('render_kw', {}).update(
                # NOTE: self._prefix does not exist yet, for the shared
                #       default we assume that there is no prefix
                field.depends_on.html_data('')
            )

        yield

        # NOTE: We currently assume that the only time we have different
        #       prefixes for the same form is in a FieldList, technically
        #       we would need to always do this step below to be fully
        #       robust
        if not self._prefix:
            return

        for field_id, field in self._unbound_fields:
            if not hasattr(field, 'depends_on'):
                continue

            f = self[field_id]
            assert f.render_kw is not None
            f.render_kw = f.render_kw.copy()
            f.render_kw.update(
                field.depends_on.html_data(self._prefix)
            )

    def process_pricing(self) -> Iterator[None]:
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

    def process_discount(self) -> Iterator[None]:
        """ Processes the discount parameter on the fields, which adds the
        ability to have fields associated with a proportional discount.

        See :class:`Form` for more information.

        """

        discounts: dict[str, dict[str, Decimal]] = {}

        # move the pricing rule to the field class (happens once per class)
        for field_id, field in self._unbound_fields:
            if not hasattr(field, 'discount'):
                field.discount = field.kwargs.pop('discount', None)

        # prepare the pricing rules
        for field_id, field in self._unbound_fields:
            if field.discount:
                discounts[field_id] = {
                    key: Decimal(value)
                    for key, value in field.discount.items()
                }

        yield

        # attach the pricing rules to the field instances
        for field_id, discount in discounts.items():
            self._fields[field_id].discount = discount

    def render_display(self, field: Field) -> Markup | None:
        """ Renders the given field for display (no input). May be overwritten
        by descendants to return different html, or to return None.

        If None is returned, the field is not rendered.

        """
        if self.is_hidden(field):
            return None
        if (
            # NOTE: It's a little sus to render fields that are not part
            #       of our form at all, but for now we'll allow it.
            field.id in self
            and hasattr(self.__class__, field.id)
            and not self.is_visible_through_dependencies(field.id)
        ):
            return None
        return render_field(field)

    def is_visible_through_dependencies(self, field_id: str) -> bool:
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

    def is_hidden(self, field: Field) -> bool:
        """ True if the given field should be hidden. The effect of this is
        left to the application (it might not render the field, or add a
        class which hides the field).

        """
        return field.id in self.hidden_fields

    def hide(self, field: Field) -> None:
        """ Marks the given field as hidden. """
        self.hidden_fields.add(field.id)

    def show(self, field: Field) -> None:
        """ Marks the given field as visibile. """
        self.hidden_fields.discard(field.id)

    def prices(self) -> list[tuple[str, Price]]:
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

        currencies = {price.currency for _, price in prices}
        assert len(currencies) <= 1, 'Mixed currencies are not supported'

        return prices

    def invoice_items(
        self,
        group: str = 'form',
        cost_object: str | None = None,
        vat_rate: Decimal | None = None,
        extra: dict[str, Any] | None = None,
    ) -> list[InvoiceItemMeta]:
        """ Returns the invoice items for all selected items depending
        on the formdata. """
        return [
            InvoiceItemMeta(
                # NOTE: In some rare cases we may get a static field that has
                #       a label with a translation string instead of a static
                #       string defined through form code.
                text=label if type(label := self[field_id].label.text) is str
                           else self.request.translate(label),
                group=group,
                family=f'price-{field_id}',
                cost_object=cost_object,
                unit=price.amount,
                extra=extra,
                vat_rate=vat_rate,
            )
            for field_id, price in self.prices()
        ]

    def total(self) -> Price | None:
        """ Returns the total amount of all prices. """
        prices = self.prices()

        if not prices:
            return None

        return Price(
            sum(price.amount for field_id, price in prices),
            prices[0][1].currency,
            credit_card_payment=any(
                price.credit_card_payment
                for field_id, price in prices
            )
        )

    def discounts(self) -> list[tuple[str, Decimal]]:
        """ Returns the discounts of all selected items depending on the
        formdata. """

        discounts = []

        for field_id, field in self._fields.items():
            if not hasattr(field, 'discount') or not field.discount:
                continue

            if not self.is_visible_through_dependencies(field_id):
                continue

            values = field.data
            if not isinstance(values, list):
                values = [values]

            field_discounts = [
                discount
                for value in values
                if (discount := field.discount.get(value))
            ]
            if field_discounts:
                discount = sum(field_discounts, start=Decimal('0'))
                discounts.append((field_id, discount))

        return discounts

    def discount_items(
        self,
        group: str = 'form',
        cost_object: str | None = None,
        vat_rate: Decimal | None = None,
        extra: dict[str, Any] | None = None,
    ) -> list[InvoiceDiscountMeta]:
        """ Returns the discount items for all selected items depending
        on the formdata. """
        return [
            InvoiceDiscountMeta(
                # NOTE: In some rare cases we may get a static field that has
                #       a label with a translation string instead of a static
                #       string defined through form code.
                text=label if type(label := self[field_id].label.text) is str
                           else self.request.translate(label),
                group=group,
                family=f'discount-{field_id}',
                cost_object=cost_object,
                discount=discount,
                vat_rate=vat_rate,
                extra=extra
            )
            for field_id, discount in self.discounts()
        ]

    def total_discount(self) -> Decimal | None:
        """ Returns the total amount of all discounts.

        The discount is returned as a multiplier between `-Inf` and `1`.
        Discounts above `1` are clamped to `1`, since we can't discount
        more than 100% of the price.

        Negative discounts are allowed, but are generally discouraged.

        This discount will not be automatically be applied to the price
        of this form, since there may be external factors increasing the
        price of your submission. Also the discount may not apply to
        the options selected in the form.
        """

        discounts = self.discounts()

        total = sum(discount for field_id, discount in discounts)
        if not total:
            return None

        return min(total, Decimal('1'))

    def submitted(self, request: CoreRequest) -> bool:
        """ Returns true if the given request is a successful post request. """
        return request.POST and self.validate() or False

    def ignore_csrf_error(self) -> None:
        """ Removes the csrf error from the form if found, after validation.

        Use this only if you know what you are doing (really, never).

        """
        if self.meta.csrf_field_name in self.errors:
            del self.errors[self.meta.csrf_field_name]
            self[self.meta.csrf_field_name].errors = []

    @property
    def has_required_email_field(self) -> bool:
        """ Returns True if the form has a required e-mail field. """
        matches = self.match_fields(
            include_classes=(EmailField, ),
            required=True,
            limit=1
        )

        return matches and True or False

    @property
    def title_fields(self) -> list[str]:
        """ Fields used to generate a title. """

        return self.match_fields(
            include_classes=(StringField, ),
            exclude_classes=(TextAreaField, ),
            required=True,
            limit=3
        )

    def match_fields(
        self,
        include_classes: Iterable[type[Field]] | None = None,
        exclude_classes: Iterable[type[Field]] | None = None,
        required: bool | None = None,
        limit: int | None = None
    ) -> list[str]:
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

        # prepare arguments so they can be passed into isinstance
        if include_classes is None:
            pass
        elif not isinstance(include_classes, tuple):
            include_classes = tuple(include_classes)

        if exclude_classes is None:
            pass
        elif not isinstance(exclude_classes, tuple):
            exclude_classes = tuple(exclude_classes)

        matches = []

        for field_id, field in self._fields.items():
            if include_classes and not isinstance(field, include_classes):
                continue

            if exclude_classes and isinstance(field, exclude_classes):
                continue

            if required is None or required is self.is_required(field_id):
                pass
            else:
                continue

            matches.append(field_id)

            if limit and len(matches) == limit:
                break

        return matches

    def is_required(self, field_id: str) -> bool:
        """ Returns true if the given field_id is required. """

        for validator in self._fields[field_id].validators:
            if isinstance(validator, (InputRequired, DataRequired)):
                return True
        return False

    def get_useful_data(
        self,
        exclude: Collection[str] | None = None
    ) -> dict[str, Any]:
        """ Returns the form data in a dictionary, by default excluding data
        that should not be stored in the db backend.

        """

        honeypots = {f.name for f in self if isinstance(f, HoneyPotField)}
        exclude = exclude or {'csrf_token'}
        exclude = set(exclude) | honeypots

        return {k: v for k, v in self.data.items() if k not in exclude}

    def populate_obj(
        self,
        obj: object,
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
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

    def process(
        self,
        formdata: _MultiDictLike | None = None,
        obj: object | None = None,
        data: Mapping[str, Any] | None = None,
        extra_filters: Mapping[str, Sequence[Any]] | None = None,
        **kwargs: Any
    ) -> None:
        """ Calls :meth:`process_obj` if ``process()`` was called with
        the ``obj`` keyword argument.

        This saves an extra check in many cases where we want to extend the
        process function, but only *if* an obj has been provided.

        """
        super().process(
            formdata=formdata,
            obj=obj,
            data=data,
            extra_filters=extra_filters,
            **kwargs
        )

        if obj is not None:
            self.process_obj(obj)

    def process_obj(self, obj: object) -> None:
        """ Called by :meth:`process` if an object was passed.

        Do *not* use this function directly. To process an object, you should
        call ``form.process(obj=obj)`` instead.

        """

    def delete_field(self, fieldname: str) -> None:
        """ Removes the given field from the form and all the fieldsets. """

        def fieldsets_without_field() -> Iterator[Fieldset]:
            for fieldset in self.fieldsets:
                if fieldname in fieldset.fields:
                    del fieldset.fields[fieldname]

                if fieldset.fields:
                    yield fieldset

        self.fieldsets = list(fieldsets_without_field())

        del self[fieldname]

    def validate(
        self,
        extra_validators: Mapping[str, Sequence[Any]] | None = None
    ) -> bool:
        """ Adds support for 'ensurances' to the form. An ensurance is a
        method which is called during validation when all the fields have
        been populated. Therefore it is a good place to validate against
        multiple fields.

        All methods which start with ``ensure_`` are ensurances. If and only if
        an ensurance returns False it is considered to have failed. In this
        case the validate method returns False as well. If None or '' or
        any other falsy value is returned, no error is assumed! This avoids
        having to return an extra True at the end of each ensurance.

        When one ensurance fails, the others are still run. Also, there's no
        error display mechanism. Showing an error is left to the ensurance
        itself. It can do so by adding messages to the various error lists
        of the form or by showing an alert through the request.

        """
        result = super().validate(extra_validators=extra_validators)

        for ensurance in self.ensurances:
            if ensurance() is False:
                result = False

        return result

    @property
    def ensurances(self) -> Iterator[Callable[[], bool]]:
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

    @staticmethod
    def as_maybe_markdown(raw_text: str) -> tuple[str, bool]:
        md = render_md(raw_text)
        stripped = md.strip().replace(
            Markup('<p>'), '').replace(Markup('</p>'), '')
        # has markdown elements
        if stripped != raw_text:
            return md, True
        return raw_text, False

    def additional_field_help(
        self,
        field: Field,
        length_limit: int = 54
    ) -> str | None:
        """ Returns the field description in modified form if
        the description should be rendered separately in the field macro.
        """
        if hasattr(field, 'long_description'):
            return field.long_description
        if 'long_description' in (getattr(field, 'render_kw', {}) or {}):
            return field.render_kw['long_description']
        if not field.description:
            return None
        desc, is_md = Form.as_maybe_markdown(
            self.request.translate(field.description)
        )
        if is_md or len(desc) > length_limit:
            return desc
        if field.type in FIELDS_NO_RENDERED_PLACEHOLDER:
            return desc
        return None


class Fieldset:
    """ Defines a fieldset with a list of fields. """

    fields: dict[str, CallableProxyType[Field]]

    def __init__(self, label: str | None, fields: Iterable[Field]):
        """ Initializes the Fieldset.

        :label: Label of the fieldset (None if it's an invisible fieldset)
        :fields: Iterator of bound fields. Fieldset creates a list of weak
        references to these fields, as they are defined elsewhere and should
        not be kept in memory just because a Fieldset references them.

        """
        self.label = label
        self.fields = OrderedDict((f.id, weakref.proxy(f)) for f in fields)

    def __len__(self) -> int:
        return len(self.fields)

    def __getitem__(self, key: str) -> CallableProxyType[Field]:
        return self.fields[key]

    @property
    def is_visible(self) -> bool:
        return self.label is not None

    @property
    def non_empty_fields(self) -> dict[str, CallableProxyType[Field]]:
        """ Returns only the fields which are not empty. """
        return OrderedDict(
            (id, field) for id, field in self.fields.items() if field.data)


class FieldDependency:
    """ Defines a dependency to a field. The given field(s) must have the given
    choice for this dependency to be fulfilled.

    It's possible to depend on NOT the given value by preceeding it with a '!':

        FieldDependency('field_1', '!choice_1')

    To depend on more than one field, add the field_id's and choices to the
    constructor:

        FieldDependency('field_1', 'choice_1')
        FieldDependency('field_1', 'choice_1', 'field_2', 'choice_2')

    """

    dependencies: list[DependencyDict]

    def __init__(self, *kwargs: object):
        assert len(kwargs) and not len(kwargs) % 2

        self.dependencies = []
        for field_id, raw_choice in zip(kwargs[::2], kwargs[1::2]):
            assert isinstance(field_id, str)
            choice = raw_choice
            if isinstance(choice, str):
                invert = choice.startswith('!')
                if invert:
                    choice = choice[1:]
            else:
                invert = False

            # NOTE: Fields in WTForms can't store an empty string, they
            #       will instead be normalized to None, the raw_choice
            #       should stay the same however, since the input in the
            #       form will have an empty string as its value
            if raw_choice == '':
                choice = None

            self.dependencies.append({
                'field_id': field_id,
                'raw_choice': raw_choice,
                'invert': invert,
                'choice': choice,
            })

    def fulfilled(self, form: Form, field: Field) -> bool:
        result = True
        for dependency in self.dependencies:
            data = getattr(form, dependency['field_id']).data
            choice = dependency['choice']
            invert = dependency['invert']

            if isinstance(data, bool) and choice in ('y', 'n'):
                choice = choice == 'y' and True or False

            result = result and ((data == choice) ^ invert)
        return result

    def unfulfilled(self, form: Form, field: Field) -> bool:
        return not self.fulfilled(form, field)

    @property
    def field_id(self) -> str:
        return self.dependencies[0]['field_id']

    def html_data(self, prefix: str) -> dict[str, str]:
        value = ';'.join(
            f"{prefix}{d['field_id']}/{d['raw_choice']}"
            for d in self.dependencies
        )

        return {'data-depends-on': value}


class Pricing:
    """ Defines pricing on a field, returning the correct price for the field
    depending on its rule.

    """

    def __init__(self, rules: PricingRules):
        self.rules = {
            rule: Price(
                amount,
                currency,
                credit_card_payment=extra[0] if extra else False,
            )
            for rule, (amount, currency, *extra) in rules.items()
        }

    @property
    def has_payment_rule(self) -> bool:
        return any(
            price.credit_card_payment for price in self.rules.values()
        )

    def price(self, field: Field) -> Price | None:
        values = field.data
        if not isinstance(field.data, list):
            values = [values]

        total = None
        credit_card_payment = False
        for value in values:
            price = self.rules.get(value, None)
            amount = None

            if price is not None:
                amount = price.amount
            elif isinstance(value, int):
                # check integer ranges (for integer range fields)
                for key, price in self.rules.items():
                    if not isinstance(key, range):
                        continue

                    # python ranges exclude stop, but form ranges include them
                    if value in key or value == key.stop:
                        if value != 0:
                            # we special case this, because we don't
                            # want to e.g. require credit card payments
                            # if 0 items have been selected
                            amount = price.amount * value
                        break

            if amount is not None:
                assert price is not None
                total = (total or Decimal(0)) + amount
                currency = price.currency
                if price.credit_card_payment is True:
                    credit_card_payment = True

        if total is None:
            return None
        else:
            return Price(
                total,
                currency,
                credit_card_payment=credit_card_payment
            )


# TODO: We should create a mypy plugin that properly infers the return-type
#       this will also take care of dynamic base class errors. For now we
#       forward the type of the first form that was passed in
def merge_forms(form: type[_FormT], /, *forms: type[Form]) -> type[_FormT]:
    """ Takes a list of forms and merges them.

    In doing so, a new class is created which inherits from all the forms in
    the default method resolution order. So the first class will override
    fields in the second class and so on.

    So this method is basically the same as::

        class Merged(*forms):
            pass

    With *one crucial difference*, the order of the fields is as follows:

    First, the fields from the first form are rendered, then the fields
    from the second form and so on. This is not the case if you merge the
    forms by simple class inheritance, as each form has it's own internal
    field order, which when merged leads to unexpected results.

    """

    class MergedForm(form, *forms):  # type:ignore
        pass

    all_forms: Iterable[type[Form]] = chain((form, ), forms)
    fields_in_order = (
        name
        for cls in all_forms
        for name, field in utils.get_fields_from_class(cls)
    )

    return enforce_order(MergedForm, fields_in_order)


def enforce_order(
    form_class: type[_FormT],
    fields_in_order: Iterable[str]
) -> type[_FormT]:
    """ Takes a list of fields used in a form_class and enforces the
    order of those fields.

    If not all fields in the form are given, the resulting order is undefined.

    """

    # XXX to make sure the field order of the existing class remains
    # unchanged, we need to instantiate the class once (wtforms seems
    # to do some housekeeping somewhere)
    form_class()

    class EnforcedOrderForm(form_class):  # type:ignore
        pass

    processed = set()

    for counter, name in enumerate(fields_in_order, start=1):
        if name in processed:
            continue

        getattr(EnforcedOrderForm, name).creation_counter = counter
        processed.add(name)

    return EnforcedOrderForm


def move_fields(
    form_class: type[_FormT],
    fields: Collection[str],
    after: str | None = None,
    before: str | None = None,
) -> type[_FormT]:
    """ Reorders the given fields (given by name) by inserting them directly
    after the given field.

    If ``after`` and ``before`` are ``None``, the fields are moved to the end.

    """

    fields_in_order: list[str] = []

    for name, _ in utils.get_fields_from_class(form_class):
        if name in fields:
            continue

        if name == before:
            fields_in_order.extend(fields)

        fields_in_order.append(name)

        if name == after:
            fields_in_order.extend(fields)

    if after is None and before is None:
        fields_in_order.extend(fields)

    return enforce_order(form_class, fields_in_order)
