class Searchable(object):
    """ Defines the interface required for an object to be searchable. """

    @property
    def es_properties(self):
        """ Returns the type mapping of this model. Each property in the
        mapping will be read from the model instance.

        The returned object needs to be a dict or an object that provides
        a ``to_dict`` method.

        """
        raise NotImplementedError

    @property
    def es_language(self):
        """ Returns the ISO 639-1 language code of the content. """
        raise NotImplementedError

    @property
    def es_type_name(self):
        """ Returns the unique type name of the model. """
        raise NotImplementedError
