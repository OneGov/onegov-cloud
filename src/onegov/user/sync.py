from __future__ import annotations

from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence
    from ldap3 import Entry
    from typing import NotRequired, TypedDict

    class UserSourceArgsWithoutName(TypedDict):
        bases: Sequence[str]
        # FIXME: We should probably make this generic in Org
        org: NotRequired[Any]
        filters: NotRequired[Sequence[str]]
        user_type: NotRequired[str]
        default_filter: NotRequired[str]


_T = TypeVar('_T')


# FIXME: Should we use `click.echo` or `log.info` instead of `print`?
class UserSource:
    """ Generalized UserSource to facilitate ldap sync """

    def __init__(
        self,
        name: str,
        bases: Sequence[str],
        # FIXME: We should probably make this generic in Org or
        #        drop this entirely if we don't use it anywhere
        org: Any | None = None,
        filters: Sequence[str] | None = None,
        user_type: str | None = None,
        default_filter: str = '(objectClass=*)',
        verbose: bool = False
    ):
        self.name = name.lower()
        self._bases = bases
        self.default_filter = default_filter

        if filters:
            assert len(filters) == len(bases)

        self.filters = filters or self.default_filters
        self._org = org
        self._user_type = user_type
        self.verbose = verbose

    @overload
    @staticmethod
    def scalar(value: list[str] | str | None, default: str = '') -> str: ...
    @overload
    @staticmethod
    def scalar(value: list[_T] | _T | None, default: _T) -> _T: ...

    @staticmethod
    def scalar(value: list[Any] | Any | None, default: Any = '') -> Any:
        if value and isinstance(value, list):
            return value[0]
        return value or default

    @property
    def ldap_attributes(self) -> Sequence[str]:
        raise NotImplementedError

    @property
    def ldap_mapping(self) -> Mapping[str, str]:
        raise NotImplementedError

    @property
    def organisation(self) -> Any:
        return getattr(self, f'org_{self.name}', self._org)

    @property
    def bases(self) -> Sequence[str]:
        return getattr(self, f'bases_{self.name}', self._bases)

    def user_type_default(self, entry: Entry) -> str | None:
        return self._user_type

    def user_type(self, entry: Entry) -> str | None:
        func = getattr(self, f'user_type_{self.name}', None)
        return func(entry) if func else self.user_type_default(entry)

    def excluded_default(self, entry: Entry) -> bool:
        """ Default when no function specific to the source name exists. """
        return False

    def excluded(self, entry: Entry) -> bool:
        """ Finds a specific exclusion function specific to the name or use
        the fallback """
        func = getattr(self, f'exclude_{self.name}', None)
        return func(entry) if func else self.excluded_default(entry)

    @property
    def default_filters(self) -> list[str]:
        return [self.default_filter for i in range(len(self.bases))]

    @property
    def bases_filters_attributes(
        self
    ) -> Sequence[tuple[str, str, Sequence[str]]]:
        return tuple(
            (b, f, self.ldap_attributes)
            for b, f in zip(self.bases, self.filters)
        )

    def map_entry(self, entry: Entry) -> dict[str, Any]:
        attrs = entry.entry_attributes_as_dict
        user = {
            column: self.scalar(attrs.get(attr))
            for attr, column in self.ldap_mapping.items()
        }
        return user

    def complete_entry(
        self,
        user: dict[str, Any],
        **kwargs: Any
    ) -> dict[str, Any]:
        """ Add additional logic after the user is mapped before writing to
        the db. """
        return user

    def map_entries(
        self,
        entries: Iterable[Entry],
        **kwargs: Any
    ) -> Iterator[dict[str, Any]]:
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

    schools: dict[str, UserSourceArgsWithoutName] = {
        'PHZ': {
            'default_filter': '(mail=*@phzg.ch)',
            'org': 'DBK / AMH / Pädagogische Hochschule Zug',
            'bases': ['o=KTZG', 'o=Extern']
        },
        'ABA': {
            'default_filter': '(mail=*@aba-zug.ch)',
            'org': 'VD / ABA',
            'bases': ['ou=aba,ou=SchulNet,o=Extern']
        },
        'FMS': {
            'default_filter': '(mail=*@fms-zg.ch)',
            'org': 'DBK / AMH / Fachmittelschule Zug',
            'bases': ['ou=fms,ou=SchulNet,o=Extern']
        },
        'KBZ': {
            'default_filter': '(mail=*@kbz-zug.ch)',
            'org': 'VD / KBZ',
            'bases': ['ou=kbz,ou=SchulNet,o=Extern']
        },
        'KSM': {
            'default_filter': '(mail=*@ksmenzingen.ch)',
            'org': 'DBK / AMH / Kantonsschule Menzingen',
            'bases': ['ou=ksm,ou=SchulNet,o=Extern']
        },
        'KSZ': {
            'default_filter': '(mail=*@ksz.ch)',
            'org': 'DBK / AMH / Kantonsschule Zug',
            'bases': ['ou=ksz,ou=SchulNet,o=Extern']
        },
        'GIBZ': {
            'default_filter': '(mail=*@gibz.ch)',
            'org': 'VD / GIBZ',
            'bases': ['ou=gibz,ou=SchulNet,o=Extern']
        }
    }

    ldap_users: dict[str, UserSourceArgsWithoutName] = {
        'KTZG': {'bases': ['ou=Kanton,o=KTZG']}
    }

    @property
    def ldap_attributes(self) -> list[str]:
        additional = ['groupMembership']
        if any('schulnet' in b.lower() for b in self.bases):
            additional.append('zgXServiceSubscription')
        return [
            *self.ldap_mapping.keys(),
            *additional
        ]

    def user_type_ktzg(self, entry: Entry) -> str | None:
        """ KTZG specific user type """
        mail = entry.entry_attributes_as_dict.get('mail')
        mail = mail and mail[0].strip().lower()
        if mail and mail.endswith('@zg.ch'):
            return 'ldap'
        elif self.verbose:
            print(f'No usertype for {mail}')  # noqa: T201
        return None

    def user_type_default(self, entry: Entry) -> str | None:
        """For all the schools, we filter by Mail already, but we exclude the
        students. Name specific user_type functions will run first, this is
        a fallback. """
        attrs = entry.entry_attributes_as_dict
        reasons = attrs.get('zgXServiceSubscription', [])
        reasons = [r.lower() for r in reasons]

        if 'student' in reasons:
            if self.verbose:
                print('Skip: no user_type for student')  # noqa: T201
            return None

        return 'regular'

    def excluded(self, entry: Entry) -> bool:
        """General exclusion pattern for all synced users. """
        data = entry.entry_attributes_as_dict
        mail = data.get('mail')

        if not mail or not mail[0].strip():
            if self.verbose:
                print('Excluded: No Mail')  # noqa: T201
            return True

        if entry.entry_dn.count(',') <= 1:
            if self.verbose:
                print(f'Excluded entry_dn.count(",") <= 1: {mail!s}')  # noqa: T201
            return True

        if 'ou=HRdeleted' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded HRdeleted: {mail!s}')  # noqa: T201
            return True

        if 'ou=Other' in entry.entry_dn:
            if self.verbose:
                print(f'Excluded ou=Other: {mail!s}')  # noqa: T201
            return True

        if not self.user_type(entry):
            return True

        # call exclude functions specific to the name of the source
        # if there is any, else return False
        return super().excluded(entry)

    def map_entry(self, entry: Entry) -> dict[str, Any]:
        attrs = entry.entry_attributes_as_dict

        user: dict[str, Any] = {
            column: self.scalar(attrs.get(attr))
            for attr, column in self.ldap_mapping.items()
        }

        user['mail'] = user['mail'].lower().strip()
        user['groups'] = {g.lower() for g in attrs['groupMembership']}
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

    def complete_entry(
        self,
        user: dict[str, Any],
        **kwargs: Any
    ) -> dict[str, Any]:
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

    def map_entries(
        self,
        entries: Iterable[Entry],
        **kwargs: Any
    ) -> Iterator[dict[str, Any]]:

        count = 0
        total = 0
        sf = kwargs.pop('search_filter')
        base = kwargs.pop('base')

        for e in entries:
            total += 1
            if self.excluded(e):
                continue

            count += 1
            yield self.complete_entry(self.map_entry(e), **kwargs)
        if self.verbose:
            print(f'Base: {base}\t\tFilter: {sf}')  # noqa: T201
            print(f'- Total: {total}')  # noqa: T201
            print(f'- Found: {count}')  # noqa: T201
            print(f'- Excluded: {total - count}')  # noqa: T201

    @classmethod
    def factory(cls, verbose: bool = False) -> list[ZugUserSource]:
        # FIXME: Why are we using ZugUserSource and not cls?
        #        Switch to list[Self] if we decide to change this
        return [
            *(ZugUserSource(name, verbose=verbose, **entry)
              for name, entry in cls.schools.items()),
            *(ZugUserSource(name, verbose=verbose, **entry)
              for name, entry in cls.ldap_users.items())
        ]
