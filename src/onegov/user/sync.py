
class UserSource:
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


class ZugUserSource(UserSource):

    default_filter = '(objectClass=*)'
    ldap_mapping = {
        'uid': 'source_id',
        'zgXGivenName': 'first_name',
        'zgXSurname': 'last_name',
        'mail': 'mail',
        'zgXDirektionAbk': 'directorate',
        'zgXAmtAbk': 'agency',
        'zgXAbteilung': 'department',
    }

    schools = dict(
        PHZ={
            'default_filter': '(mail=*@phzg.ch)',
            'org': 'DBK / AMH / Pädagogische Hochschule Zug',
            'bases': ['o=KTZG', 'o=Extern']
        },
        ABA={
            'default_filter': '(mail=*@aba-zug.ch)',
            'org': 'VD / ABA',
            'bases': ['ou=aba,ou=SchulNet,o=Extern']
        },
        FMS={
            'default_filter': '(mail=*@fms-zg.ch)',
            'org': 'DBK / AMH / Fachmittelschule Zug',
            'bases': ['ou=fms,ou=SchulNet,o=Extern']
        },
        KBZ={
            'default_filter': '(mail=*@kbz-zug.ch)',
            'org': 'VD / KBZ',
            'bases': ['ou=kbz,ou=SchulNet,o=Extern']
        },
        KSM={
            'default_filter': '(mail=*@ksmenzingen.ch)',
            'org': 'DBK / AMH / Kantonsschule Menzingen',
            'bases': ['ou=ksm,ou=SchulNet,o=Extern']
        },
        KSZ={
            'default_filter': '(mail=*@ksz.ch)',
            'org': 'DBK / AMH / Kantonsschule Zug',
            'bases': ['ou=ksz,ou=SchulNet,o=Extern']
        },
        GIBZ={
            'default_filter': '(mail=*@gibz.ch)',
            'org': 'VD / GIBZ',
            'bases': ['ou=gibz,ou=SchulNet,o=Extern']
        }
    )

    ldap_users = dict(KTZG={'bases': ['ou=Kanton,o=KTZG']})

    @property
    def ldap_attributes(self):
        additional = ['groupMembership']
        if any(('schulnet' in b.lower() for b in self.bases)):
            additional.append('zgXServiceSubscription')
        return [
            *self.ldap_mapping.keys(),
            *additional
        ]

    def user_type_ktzg(self, entry):
        """ KTZG specific user type """
        mail = entry.entry_attributes_as_dict.get('mail')
        mail = mail and mail[0].strip().lower()
        if mail and mail.endswith('@zg.ch'):
            return 'ldap'
        elif self.verbose:
            print(f'No usertype for {mail}')

    def user_type_default(self, entry):
        """For all the schools, we filter by Mail already, but we exclude the
        students. Name specific user_type functions will run first, this is
         a fallback. """
        attrs = entry.entry_attributes_as_dict
        reasons = attrs.get('zgXServiceSubscription', [])
        reasons = [r.lower() for r in reasons]

        if 'student' in reasons:
            if self.verbose:
                print('Skip: no user_type for student')
            return None

        return 'regular'

    def excluded(self, entry):
        """General exclusion pattern for all synced users. """
        data = entry.entry_attributes_as_dict
        mail = data.get('mail')

        if not mail or not mail[0].strip():
            if self.verbose:
                print('Excluded: No Mail')
            return True

        if entry.entry_dn.count(',') <= 1:
            if self.verbose:
                print(f'Excluded entry_dn.count(",") <= 1: {str(mail)}')
            return True

        if 'ou=HRdeleted' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded HRdeleted: {str(mail)}')
            return True

        if 'ou=Other' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded ou=Other: {str(mail)}')
            return True

        if not self.user_type(entry):
            return True

        # call exclude functions specific to the name of the source
        # if there is any, else return False
        return super().excluded(entry)

    def map_entry(self, entry):
        attrs = entry.entry_attributes_as_dict

        user = {
            column: self.scalar(attrs.get(attr))
            for attr, column in self.ldap_mapping.items()
        }

        user['mail'] = user['mail'].lower().strip()
        user['groups'] = set(g.lower() for g in attrs['groupMembership'])
        user['type'] = self.user_type(entry)

        if user['type'] == 'ldap':
            user['organisation'] = ' / '.join(o for o in (
                user['directorate'],
                user['agency'],
                user['department']
            ) if o)
        elif user['type'] == 'regular':
            domain = self.organisation
            assert domain is not None
            user['organisation'] = domain
        else:
            raise NotImplementedError()

        return user

    def complete_entry(self, user, **kwargs):
        if user['type'] == 'ldap':
            if kwargs['admin_group'] in user['groups']:
                user['role'] = 'admin'
            elif kwargs['editor_group'] in user['groups']:
                user['role'] = 'editor'
            else:
                user['role'] = 'member'
        else:
            user['role'] = 'member'
        return user

    def map_entries(self, entries, **kwargs):
        count = 0
        total = 0
        sf = kwargs.pop('search_filter')
        base = kwargs.pop('base')

        for e in entries:
            total += 1
            if self.excluded(e):
                continue

            count += 1
            user = self.complete_entry(self.map_entry(e), **kwargs)

            yield user
        if self.verbose:
            print(f'Base: {base}\t\tFilter: {sf}')
            print(f'- Total: {total}')
            print(f'- Found: {count}')
            print(f'- Excluded: {total - count}')

    @classmethod
    def factory(cls, verbose=False):
        return [
            *(ZugUserSource(name, verbose=verbose, **entry)
              for name, entry in cls.schools.items()),
            *(ZugUserSource(name, verbose=verbose, **entry)
              for name, entry in cls.ldap_users.items())
        ]
