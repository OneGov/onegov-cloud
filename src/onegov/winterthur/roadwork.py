from __future__ import annotations

import isodate
import pycurl
import sedate

from datetime import datetime, timedelta
from dogpile.cache.api import NO_VALUE
from functools import cached_property
from io import BytesIO
from onegov.core.custom import json
from operator import attrgetter
from pathlib import Path
from purl import URL
from sedate import utcnow


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.cache import RedisCacheRegion
    from typing import Self


class RoadworkError(Exception):
    pass


class RoadworkConnectionError(RoadworkError):
    pass


class RoadworkConfig:
    """ Looks at ~/.pdb.secret and /etc/pdb.secret (in this order), to extract
    the configuration used for the RoadworkClient class.

    The configuration is as follows::

        HOSTNAME: pdb.example.org
        ENDPOINT: 127.0.0.1:6004
        USERNAME: username
        PASSWORD: password

    * The HOSTNAME is the address of the PDB service.
    * The ENDPOINT is the optional address of the tcp-proxy used.
    * The USERNAME is the NTLM password.
    * The PASSWORD is the NTLM password.

    """

    def __init__(
        self,
        hostname: str | None,
        endpoint: str | None,
        username: str | None,
        password: str | None
    ) -> None:
        self.hostname = hostname
        self.endpoint = endpoint
        self.username = username
        self.password = password

    @classmethod
    def lookup_paths(cls) -> Iterator[Path]:
        yield Path('~/.pdb.secret').expanduser()
        yield Path('/etc/pdb.secret')

    @classmethod
    def lookup(cls) -> Self:
        for path in cls.lookup_paths():
            if path.exists():
                return cls(**cls.parse(path))

        paths = ', '.join(str(p) for p in cls.lookup_paths())
        raise RoadworkError(
            f'No pdb configuration found in {paths}')

    @classmethod
    def parse(cls, path: Path) -> dict[str, str | None]:
        result: dict[str, str | None] = {
            'hostname': None,
            'endpoint': None,
            'username': None,
            'password': None,  # nosec: B105
        }

        with path.open('r') as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                if ':' not in line:
                    continue

                if line.startswith('#'):
                    continue

                k, v = line.split(':', maxsplit=1)
                k = k.strip().lower()
                v = v.strip()

                if k in result:
                    result[k] = v

        return result


class RoadworkClient:
    """ A proxy to Winterthur's internal roadworks service. Uses redis as
    a caching mechanism to ensure performance and reliability.

    Since the roadworks service can only be reached inside Winterthur's
    network, we rely on a proxy connection during development/testing.

    To not expose any information unwittingly to the public, the description
    of how to connect to that proxy is kept at docs.seantis.ch.

    """

    def __init__(
        self,
        cache: RedisCacheRegion,
        hostname: str,
        username: str,
        password: str,
        endpoint: str | None = None
    ) -> None:
        self.cache = cache
        self.hostname = hostname
        self.username = username
        self.password = password
        self.endpoint = endpoint or hostname

    @cached_property
    def curl(self) -> pycurl.Curl:
        curl = pycurl.Curl()
        curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
        curl.setopt(pycurl.USERPWD, f'{self.username}:{self.password}')
        curl.setopt(pycurl.HTTPHEADER, [f'HOST: {self.hostname}'])
        curl.setopt(pycurl.VERBOSE, True)
        # This is is not really a good idea as it disables TLS certificate
        # validation!
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        return curl

    def url(self, path: str) -> str:
        return f'https://{self.endpoint}/{path}'

    def get(
        self,
        path: str,
        lifetime: float = 5 * 60,
        downtime: float = 60 * 60
    ) -> Any:
        """ Requests the given path, returning the resulting json if
        successful.

        A cache is used in two stages:

        * At the lifetime stage, the cache is returned unconditionally.
        * At the end of the lifetime, the cache is refreshed if possible.
        * At the end of the downtime stage the cache forcefully refreshed.

        During its lifetime the object is basically up to 5 minutes out of
        date. But since the backend may not be available when that time
        expires we operate with a downtime that is higher (1 hour).

        This means that a downtime in the backend will not result in evicted
        caches, even if the lifetime is up. Once the downtime limit is up we
        do however evict the cache forcefully, raising an error if we cannot
        connect to the backend.

        """
        path = path.lstrip('/')
        cached = self.cache.get(path)

        def refresh() -> Any:
            try:
                status, body = self.get_uncached(path)
            except pycurl.error as exception:
                raise RoadworkConnectionError(
                    f'Could not connect to {self.hostname}'
                ) from exception

            if status == 200:
                self.cache.set(path, {
                    'created': utcnow(),
                    'status': status,
                    'body': body
                })

                return body

            raise RoadworkError(f'{path} returned {status}')

        # no cache yet, return result and cache it
        if cached is NO_VALUE:
            return refresh()

        now = utcnow()
        lifetime_horizon = cached['created'] + timedelta(seconds=lifetime)
        downtime_horizon = cached['created'] + timedelta(seconds=downtime)

        # within cache lifetime, return cached value
        if now <= lifetime_horizon:
            return cached['body']

        # outside cache lifetime, but still in downtime horizon, try to
        # refresh the value but ignore errors
        if lifetime_horizon < now < downtime_horizon:
            try:
                return refresh()
            except RoadworkConnectionError:
                return cached['body']

        # outside the downtime lifetime, force refresh and raise errors
        return refresh()

    def get_uncached(self, path: str) -> tuple[int, Any]:
        body = BytesIO()

        self.curl.setopt(pycurl.URL, self.url(path))
        self.curl.setopt(pycurl.WRITEFUNCTION, body.write)
        self.curl.perform()

        status = self.curl.getinfo(pycurl.RESPONSE_CODE)
        body_str = body.getvalue().decode('utf-8')

        if status == 200:
            return status, json.loads(body_str)

        return status, body_str

    def is_cacheable(self, response: tuple[int, Any]) -> bool:
        return response[0] == 200


class RoadworkCollection:

    def __init__(
        self,
        client: RoadworkClient,
        letter: str | None = None,
        query: str | None = None
    ) -> None:
        self.client = client
        self.query = None
        self.letter = None

        if query:
            self.query = query.lower()

        elif letter:
            self.letter = letter.lower()

    @property
    def letters(self) -> list[str]:
        return sorted({
            letter
            for roadwork in self.by_letter(None).roadwork
            for letter in roadwork.letters
        })

    def by_filter(self, filter: str) -> list[Roadwork]:

        # note: addGisLink doesn't work here
        url = (
            URL('odata/Baustellen')
            .query_param('addGisLink', 'False')
            .query_param('$filter', filter)
        )

        records = self.client.get(url.as_string()).get('value', ())
        return sorted((
            Roadwork(r) for r in records
            if r['Internet']
        ), key=attrgetter('title'))

    @property
    def roadwork(self) -> list[Roadwork]:
        date = datetime.today()

        roadwork = self.by_filter(filter=' and '.join((
            f'DauerVon le {date.strftime("%Y-%m-%d")}',
            f'DauerBis ge {date.strftime("%Y-%m-%d")}',
        )))

        # The backend supports searches/filters, but the used dataset is
        # so small that it makes little sense to use that feature, since it
        # would lead to a lot more cache-misses on our end.
        #
        # Instead we simply loop through the results and filter them out.
        if self.query:
            roadwork = [
                r for r in roadwork if self.query in r.title.lower()
            ]

        elif self.letter:
            roadwork = [
                r for r in roadwork if self.letter in r.letters
            ]

        return roadwork

    def by_id(self, id: int) -> Roadwork | None:
        url = (
            URL(f'odata/Baustellen({id})')
            .query_param('addGisLink', 'True'))

        work = tuple(
            Roadwork(r) for r in self.client.get(
                url.as_string()).get('value', ()))

        if work:
            return work[0]

        # secondary lookup is against the subsections.. this probably calls
        # for an index eventually
        for r in self.roadwork:
            for section in r.sections:
                if section.id == id:
                    return section
        return None

    def by_letter(self, letter: str | None) -> Self:
        return self.__class__(self.client, letter=letter, query=None)


class Roadwork:

    convertors: dict[str, Callable[[str | None], Any]]

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

        self.convertors = {
            'DauerVon': lambda v: v and isodate.parse_datetime(v),
            'DauerBis': lambda v: v and isodate.parse_datetime(v),
        }

    @property
    def id(self) -> int:
        return self['Id']

    @property
    def letters(self) -> Iterator[str]:
        for key in ('ProjektBezeichnung', 'ProjektBereich'):
            if value := self[key]:
                letter = value[0].lower()
                if 97 <= ord(letter) <= 122:
                    yield letter

    @property
    def title(self) -> str:
        parts = (self[key] for key in ('ProjektBezeichnung', 'ProjektBereich'))
        parts = (p.strip() for p in parts if p)
        parts = (p for p in parts)

        return ' '.join(parts)

    @property
    def sections(self) -> list[Self]:
        now = sedate.utcnow()

        sections = (
            self.__class__({
                'Id': r['TeilbaustelleId'],
                'Teilbaustellen': [],
                **r
            }) for r in self['Teilbaustellen']
        )

        sections = (s for s in sections if s['DauerVon'])
        sections = (s for s in sections if s['DauerVon'] <= now)
        sections = (s for s in sections if now <= (s['DauerBis'] or now))

        return list(sections)

    def __getitem__(self, key: str) -> Any:
        value = self.data[key]

        if key in self.convertors:
            return self.convertors[key](value)

        return value

    def __contains__(self, key: str) -> bool:
        return key in self.data
