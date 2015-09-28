from onegov.search.utils import classproperty


class Searchable(object):
    """ Defines the interface required for an object to be searchable.

    Note that ``es_id ``, ``es_properties`` and ``es_type_name`` must be class
    properties, not instance properties. So do this::

        class X(Searchable):

            es_properties = {}
            es_type_name = 'x'

    But do not do this::

        class X(Searchable):

            @property
            def es_properties(self):
                return {}

            @property
            def es_type_name(self):
                return 'x'

    The rest of the properties may be normal properties.

    Polymorphic Identities
    ======================

    If SQLAlchemy's Polymorphic Identities are used, each identity must
    have it's own unqiue ``es_type_name``. Though such models may share
    the ``es_properties`` from the base class, we don't assume anything and
    store each polymorphic identity in its own index.

    From the point of view of elasticsearch, each different polymorphic
    identity is a completely different model.

    """

    @classproperty
    def es_properties(self):
        """ Returns the type mapping of this model. Each property in the
        mapping will be read from the model instance.

        The returned object needs to be a dict or an object that provides
        a ``to_dict`` method.

        Internally, onegov.search stores differing languages in different
        indices. For this reason you should mark all fields which are
        specific to :attr:`es_language` like this::

            @property
            def es_properties(self):

                return {
                    'title': { 'type': 'localized' }
                }

        Onegov.search will automatically insert the right analyzer for
        types like these.

        There's currently only limited support for properties here, namely
        objects and nested mappings do not work! This is going to be added
        in the future though.

        """
        raise NotImplementedError

    @classproperty
    def es_type_name(self):
        """ Returns the unique type name of the model. """
        raise NotImplementedError

    @classproperty
    def es_id(self):
        """ The name of the id attribute (not the actual value!).

        If you use this on an ORM model, be sure to use a primary key, all
        other properties are not available during deletion.

        """
        raise NotImplementedError

    @property
    def es_language(self):
        """ Returns the ISO 639-1 language code of the content. Note that
        the object's id may not be the same over differing languages.

        That is to say, this is not valid::

            Object(id=1, language='de')
            Object(id=2, language='en')

        """
        raise NotImplementedError

    @property
    def es_public(self):
        """ Returns True if the model is available to be found by the public.
        If false, only editors/admins will see this object in the search
        results.

        """
        raise NotImplementedError

    @property
    def es_skip(self):
        """ Returns True if the indexing of this specific model instance
        should be skipped. """
        return False

    @property
    def es_suggestion(self):
        """ Returns suggest-as-you-type value of the document.
        The field used for this property should also be indexed, or the
        suggestion will lead to nowhere.

        If a single string is returned, the completion input equals the
        completion output. (My Title -> My Title)

        If an array of strings is returned, all values are possible inputs and
        the first value is the output. (My Title/Title My -> My Title)

        """
        return self.title


class ORMSearchable(Searchable):
    """ Extends the default :class:`Searchable` class with sensible defaults
    for SQLAlchemy orm models.

    """

    @classproperty
    def es_id(self):
        return 'id'

    @classproperty
    def es_type_name(self):
        return self.__tablename__
