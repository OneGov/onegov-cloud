import isodate
import pycurl
import sedate

from cached_property import cached_property
from datetime import datetime, timedelta
from io import BytesIO
from onegov.core.custom import json
from pathlib import Path
from purl import URL


class RoadworkError(Exception):
    pass


class RoadworkConnectionError(RoadworkError):
    pass


class RoadworkConfig(object):
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

    def __init__(self, hostname, endpoint, username, password):
        self.hostname = hostname
        self.endpoint = endpoint
        self.username = username
        self.password = password

    @classmethod
    def lookup_paths(self):
        yield Path('~/.pdb.secret').expanduser()
        yield Path('/etc/pdb.secret')

    @classmethod
    def lookup(cls):
        for path in cls.lookup_paths():
            if path.exists():
                return cls(**cls.parse(path))

        paths = ', '.join(str(p) for p in cls.lookup_paths())
        raise RoadworkError(
            f"No pdb configuration found in {paths}")

    @classmethod
    def parse(cls, path):
        result = {
            'hostname': None,
            'endpoint': None,
            'username': None,
            'password': None,
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


class RoadworkClient(object):
    """ A proxy to Winterthur's internal roadworks service. Uses redis as
    a caching mechanism to ensure performance and reliability.

    Since the roadworks service can only be reached inside Winterthur's
    network, we rely on a proxy connection during development/testing.

    To not expose any information unwittingly to the public, the description
    of how to connect to that proxy is kept at docs.seantis.ch.

    """

    def __init__(self, cache, hostname, username, password, endpoint=None):
        self.cache = cache
        self.hostname = hostname
        self.username = username
        self.password = password
        self.endpoint = endpoint or hostname

    @cached_property
    def curl(self):
        curl = pycurl.Curl()
        curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
        curl.setopt(pycurl.USERPWD, f"{self.username}:{self.password}")
        curl.setopt(pycurl.HTTPHEADER, [f'HOST: {self.hostname}'])

        return curl

    def url(self, path):
        return f'http://{self.endpoint}/{path}'

    def get(self, path, lifetime=5 * 60, downtime=60 * 60):
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

        def refresh():
            try:
                status, body = self.get_uncached(path)
            except pycurl.error:
                raise RoadworkConnectionError(
                    f"Could not connect to {self.hostname}")

            if status == 200:
                self.cache.set(path, {
                    'created': datetime.utcnow(),
                    'status': status,
                    'body': body
                })

                return body

            raise RoadworkError(f"{path} returned {status}")

        # no cache yet, return result and cache it
        if not cached:
            return refresh()

        now = datetime.utcnow()
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

    def get_uncached(self, path):
        body = BytesIO()

        self.curl.setopt(pycurl.URL, self.url(path))
        self.curl.setopt(pycurl.WRITEFUNCTION, body.write)
        self.curl.perform()

        status = self.curl.getinfo(pycurl.RESPONSE_CODE)
        body = body.getvalue().decode('utf-8')

        if status == 200:
            body = json.loads(body)

        return status, body

    def is_cacheable(self, response):
        return response[0] == 200


class RoadworkCollection(object):

    def __init__(self, client, letter=None, query=None):
        self.client = client
        self.query = None
        self.letter = None

        if query:
            self.query = query.lower()

        elif letter:
            self.letter = letter.lower()

    @property
    def letters(self):
        letters = set()

        for roadwork in self.by_letter(None).roadwork:
            for letter in roadwork.letters:
                letters.add(letter)

        letters = list(letters)
        letters.sort()

        return letters

    def by_filter(self, filter):

        # note: addGisLink doesn't work here
        url = URL('odata/Baustellen')\
            .query_param('addGisLink', 'False')\
            .query_param('$filter', filter)

        records = self.client.get(url.as_string()).get('value', ())
        records = (r for r in records if r['Internet'])

        work = [Roadwork(r) for r in records]
        work.sort(key=lambda r: r.title)

        return work

    @property
    def roadwork(self):
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

    def by_id(self, id):
        url = URL(f'odata/Baustellen({int(id)})')\
            .query_param('addGisLink', 'True')

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

    def by_letter(self, letter):
        return self.__class__(self.client, letter=letter, query=None)


class Roadwork(object):

    def __init__(self, data):
        self.data = data

        self.convertors = {
            'DauerVon': lambda v: v and isodate.parse_datetime(v),
            'DauerBis': lambda v: v and isodate.parse_datetime(v),
        }

    @property
    def id(self):
        return self['Id']

    @property
    def letters(self):
        for key in ('ProjektBezeichnung', 'ProjektBereich'):
            if self[key]:
                letter = self[key][0].lower()

                if letter in ('abcdefghijklmnopqrstuvwxyz'):
                    yield letter

    @property
    def title(self):
        parts = (self[key] for key in ('ProjektBezeichnung', 'ProjektBereich'))
        parts = (p.strip() for p in parts if p)
        parts = (p for p in parts)

        return ' '.join(parts)

    @property
    def sections(self):
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

    def __getitem__(self, key):
        value = self.data[key]

        if key in self.convertors:
            return self.convertors[key](value)

        return value

    def __contains__(self, key):
        return key in self.data
