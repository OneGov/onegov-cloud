from onegov.core.orm.types import JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column


IMMUTABLE_TYPES = (int, float, complex, str, tuple, frozenset, bytes)


class ContentMixin(object):
    """ Mixin providing a meta/content JSON pair. Meta is a JSON column loaded
    with each request, content is a JSON column loaded deferred (to be shown
    only in the detail view).

    """

    #: metadata associated with the form, for storing small amounts of data
    @declared_attr
    def meta(cls):
        return Column(JSON, nullable=False, default=dict)

    #: content associated with the form, for storing things like long texts
    @declared_attr
    def content(cls):
        return deferred(Column(JSON, nullable=False, default=dict))


def is_valid_default(default):
    if default is None:
        return True

    if callable(default):
        return True

    if isinstance(default, IMMUTABLE_TYPES):
        return True

    return False


class dict_property(object):
    """ Enables access of dictionaries through properties.

    Usage::

        class Model(ContentMixin):
            access_times = dict_property('meta')

    This creates a property that accesses the meta directory with the key
    'access_times'. The key is implicitly copied from the definition.

    Another way of writing this out would be::

        class Model(ContentMixin):
            access_times = dict_property('meta', 'access_times')

    As is apparent, the 'access_times' key is duplicated in this case. Usually
    you do not need to provide the name. The exception being if you want
    the property name and the dictionary key to differ::

        class Model(ContentMixin):
            access_times = dict_property('meta', 'access')

    Here, the key in the dictionary is 'access', while the property is
    'access_times'.

    Since we often use the same kind of dictionaries we can use the builtin
    properties that are scoped to a specific dictionary::

        class Model(ContentMixin):
            access_times = meta_property()

    This is equivalent to the initial example.

    We can also create our own scoped properties as follows:

        foo_property = dict_property_factory('foo')

        class Model(object):

            foo = {}

            bar = foo_property()

    Here, model.bar would read model.foo['bar'].

    Dict properties are compatible with typical python properties, so the
    usual getter/setter/deleter methods are also available::

        class Model(ContentMixin):
            content = meta_property()

            @content.setter
            def set_content(self, value):
                self.meta['content'] = value
                self.meta['content_html'] = to_html(value)

            @content.deleter
            def del_content(self):
                del self.meta['content']
                del self.meta['content_html']

    """

    def __init__(self, attribute, key=None, default=None):
        assert is_valid_default(default)
        self.attribute = attribute
        self.key = key
        self.default = default

        self.custom_getter = None
        self.custom_setter = None
        self.custom_deleter = None

    def __set_name__(self, owner, name):
        """ Sets the dictionary key, if none is provided. """

        if self.key is None:
            self.key = name

    @property
    def getter(self):
        def wrapper(fn):
            self.custom_getter = fn
            return self

        return wrapper

    @property
    def setter(self):
        def wrapper(fn):
            self.custom_setter = fn
            return self

        return wrapper

    @property
    def deleter(self):
        def wrapper(fn):
            self.custom_deleter = fn
            return self

        return wrapper

    def __get__(self, instance, owner):

        # do not implement class-only behaviour
        if instance is None:
            return

        # pass control wholly to the custom getter if available
        if self.custom_getter:
            return self.custom_getter(instance)

        # get the value in the dictionary
        data = getattr(instance, self.attribute, None)

        if data is not None and self.key in data:
            return data[self.key]

        # fallback to the default
        return self.default() if callable(self.default) else self.default

    def __set__(self, instance, value):

        # create the dictionary if it does not exist yet
        if getattr(instance, self.attribute) is None:
            setattr(instance, self.attribute, {})

        # pass control to the custom setter if available
        if self.custom_setter:
            return self.custom_setter(instance, value)

        # fallback to just setting the value
        getattr(instance, self.attribute)[self.key] = value

    def __delete__(self, instance):

        # pass control to the custom deleter if available
        if self.custom_deleter:
            return self.custom_deleter(instance)

        # fallback to just removing the value
        del getattr(instance, self.attribute)[self.key]


def dict_property_factory(attribute):
    def factory(*args, **kwargs):
        return dict_property(attribute, *args, **kwargs)

    return factory


content_property = dict_property_factory('content')
data_property = dict_property_factory('data')
meta_property = dict_property_factory('meta')

# for backwards compatibility, might be removed in the future
dictionary_based_property_factory = dict_property_factory
