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


def meta_property(name):
    """ Helper to create accessors bound to the meta attribute defined by
    :class:`ContentMixin`.

    Usage::

        class Model(ContentMixin):
            content = meta_property('content')

    This will add a content getter, setter and deleter bound, which all proxy
    to meta['content'].

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

    """

    def get_meta(self):
        return self.meta.get(name)

    def set_meta(self, value):
        self.meta[name] = value

    def del_meta(self):
        del self.meta[name]

    return property(get_meta, set_meta, del_meta)


def content_property(name):
    """ Same as :func:`meta_property`, but targeting the content dictionary.

    """

    def get_content(self):
        return self.content.get(name)

    def set_content(self, value):
        self.content[name] = value

    def del_content(self):
        del self.content[name]

    return property(get_content, set_content, del_content)
