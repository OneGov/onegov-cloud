from onegov.core.orm.types import JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column


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


def dictionary_based_property_factory(attribute):

    def dictionary_based_property(name):
        """ Enables access of dictionaries through properties.

        Usage::

            meta_property = dictionary_based_property_factory('meta')

            class Model(ContentMixin):
                content = meta_property('content')

        This will add a content getter, setter and deleter bound, which all
        proxy to meta['content'].

        Since this is just a thin wrapper around python's property we can also
        override the setter::

            class Model(ContentMixin):
                content = meta_property('content')

                @content.setter
                def set_content(self, value):
                    self.meta['content'] = value
                    self.meta['content_html'] = to_html(value)

                @content.deleter
                def del_content(self):
                    del self.meta['content']
                    del self.meta['content_html']

        meta_property and content_property, to access the
        :class:`ContentMixin`'s dictionaries are defined in this file.

        """

        def getter(self):
            dictionary = getattr(self, attribute, None)
            return dictionary.get(name) if dictionary is not None else None

        def setter(self, value):
            if getattr(self, attribute) is None:
                setattr(self, attribute, {})

            getattr(self, attribute)[name] = value

        def deleter(self):
            del getattr(self, attribute)[name]

        return property(getter, setter, deleter)

    return dictionary_based_property


meta_property = dictionary_based_property_factory('meta')
content_property = dictionary_based_property_factory('content')
