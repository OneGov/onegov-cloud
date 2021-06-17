
class UserSource(object):
    """ Generalized UserSource to facilitate ldap sync """

    def __init__(self, name, bases, org=None, filters=None, user_type=None,
                 default_filter='(objectClass=*)',
                 verbose=False):
        self.name = name.lower()
        self._bases = bases
        self.default_filter = default_filter

        if filters:
            assert len(filters) == len(bases)

        self.filters = filters or self.default_filters
        self._org = org
        self._user_type = user_type
        self.verbose = verbose

    @staticmethod
    def scalar(value, default=''):
        if value and isinstance(value, list):
            return value[0]
        return value or default

    @property
    def ldap_attributes(self):
        raise NotImplementedError

    @property
    def ldap_mapping(self):
        raise NotImplementedError

    @property
    def organisation(self):
        return getattr(self, f'org_{self.name}', self._org)

    @property
    def bases(self):
        return getattr(self, f'bases_{self.name}', self._bases)

    def user_type_default(self, entry):
        return self._user_type

    def user_type(self, entry):
        func = getattr(self, f'user_type_{self.name}', None)
        return func(entry) if func else self.user_type_default(entry)

    def excluded_default(self, entry):
        """ Default when no function specific to the source name exists. """
        return False

    def excluded(self, entry):
        """ Finds a specific exclusion function specific to the name or use
        the fallback """
        func = getattr(self, f'exclude_{self.name}', None)
        return func(entry) if func else self.excluded_default(entry)

    @property
    def default_filters(self):
        return [self.default_filter for i in range(len(self.bases))]

    @property
    def bases_filters_attributes(self):
        return tuple(
            (b, f, self.ldap_attributes)
            for b, f in zip(self.bases, self.filters)
        )

    def map_entry(self, entry):
        attrs = entry.entry_attributes_as_dict
        user = {
            column: self.scalar(attrs.get(attr))
            for attr, column in self.ldap_mapping.items()
        }
        return user

    def complete_entry(self, user, **kwargs):
        """ Add additional logic after the user is mapped before writing to
        the db. """
        return user

    def map_entries(self, entries, **kwargs):
        for e in entries:
            if self.excluded(e):
                continue

            user = self.map_entry(e)
            user = self.complete_entry(user, **kwargs)
            yield user
