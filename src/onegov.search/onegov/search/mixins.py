class Searchable(object):
    """ Defines the interface required for an object to be searchable. """

    @property
    def es_properties(self):
        """ Returns the type mapping of this model. Each property in the
        mapping will be read from the model instance.

        The returned object needs to be a dict or an object that provides
        a ``to_dict`` method.

        Internally, onegov.search stores differing languages in different
        indices. For this reason you should mark all fields which are
        specific to :attr:`es_language` like this:

            @property
            def es_properties(self):

                return {
                    'title': { 'type': 'localized' }
                }

        Onegov.search will automatically insert the right analyzer for
        types like these.

        """
        raise NotImplementedError

    @property
    def es_language(self):
        """ Returns the ISO 639-1 language code of the content. Note that
        the object's id may not be the same over differing languages.

        That is to say, this is not valid:

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

    @property
    def es_type_name(self):
        """ Returns the unique type name of the model. """
        raise NotImplementedError
