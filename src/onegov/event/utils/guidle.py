from __future__ import annotations

from bleach.sanitizer import Cleaner
from functools import cached_property
from datetime import timedelta
from dateutil.parser import parse
from onegov.gis import Coordinates
from sedate import replace_timezone


from typing import overload
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Mapping
    from collections.abc import Sequence
    from lxml.etree import _Element, _ElementTree
    from onegov.gis.models.coordinates import RealCoordinates
    from typing import TypeVar

    _T = TypeVar('_T')


class GuidleBase:
    """ Base class for parsing guidle exports containing general helpers. """

    def __init__(self, root: _Element | _ElementTree[_Element]) -> None:
        if hasattr(root, 'getroot'):
            root = root.getroot()
        self.root = root
        self.nsmap = {'guidle': 'http://www.guidle.com'}
        self.cleaner = Cleaner(
            tags=[],
            attributes={},
            strip=True,
            filters=[]
        )

    def find(
        self,
        path: str,
        root: _Element | None = None
    ) -> list[_Element]:
        """ Gets the elements with the given path. """

        root = root if root is not None else self.root
        return root.xpath(path, namespaces=self.nsmap) or []

    @overload
    def get(
        self,
        path: str,
        root: _Element | None = None,
        joiner: str = ' ',
        parser: None = None
    ) -> str: ...

    @overload
    def get(
        self,
        path: str,
        root: _Element | None = None,
        joiner: str = ' ',
        *,
        parser: Callable[[str], _T]
    ) -> _T | None: ...

    def get(
        self,
        path: str,
        root: _Element | None = None,
        joiner: str = ' ',
        parser: Callable[[str], _T] | None = None
    ) -> _T | str | None:
        """ Returns the text of the elements with the given path.

        Allows to specifiy a joining character and optionally a parser. If no
        parser is given, the text is HTML-cleaned.

        """

        result = joiner.join(
            (element.text or '').strip()
            for element in self.find(path, root)
        ).strip()

        if parser:
            return parser(result) if result else None
        else:
            return self.cleaner.clean(result) if result else ''

    def join(self, texts: Sequence[str], joiner: str = ', ') -> str:
        """ Joins a set of text, skips duplicate and empty texts while
        preserving the order. """

        deduplicated = []
        for text in texts:
            if text and text not in deduplicated:
                deduplicated.append(text)

        retval = joiner.join(deduplicated)
        return retval


class GuidleExportData(GuidleBase):
    """ Represents a whole guidle export. """

    def offers(self) -> Iterator[GuidleOffer]:
        for offer in self.find('.//guidle:offer'):
            yield GuidleOffer(offer)


class GuidleOffer(GuidleBase):
    """ Represents a single offer containing some description and dates. """

    @cached_property
    def uid(self) -> str | None:
        return self.root.get('id')

    @cached_property
    def last_update(self) -> str:
        return self.get('guidle:lastUpdateDate')

    @cached_property
    def title(self) -> str:
        title = self.get('guidle:offerDetail/guidle:title')

        # titles are rendered as unsafe html downstream, so we can
        # losen the rules one tiny bit here.

        # we'll still have '&gt,' and '&lt;', but those are probably
        # used very rarely in a title, so we can ignore that
        title = title.replace('&amp;', '&')

        return title

    @cached_property
    def description(self) -> str:
        short = self.get('guidle:offerDetail/guidle:shortDescription')
        long = self.get('guidle:offerDetail/guidle:longDescription')
        if long.startswith(short):
            short = ''

        return self.join((
            short,
            long,
            self.get('guidle:offerDetail/guidle:openingHours'),
            self.get('guidle:offerDetail/guidle:externalLink'),
            self.get('guidle:offerDetail/guidle:homepage'),
            self.get('guidle:offerDetail/guidle:ticketingUrl')
        ), '\n\n')

    @cached_property
    def price(self) -> str:
        return self.get('guidle:offerDetail/guidle:priceInformation')

    @cached_property
    def organizer(self) -> str:
        return self.join((
            self.get('guidle:contact/guidle:company'),
            self.get('guidle:contact/guidle:name'),
            self.get('guidle:contact/guidle:telephone_1'),
        ))

    @cached_property
    def organizer_email(self) -> str:
        return self.get('guidle:contact/guidle:email')

    @cached_property
    def location(self) -> str:
        return self.join((
            self.get('guidle:address/guidle:company'),
            self.get('guidle:address/guidle:street'),
            ' '.join((
                self.get('guidle:address/guidle:zip'),
                self.get('guidle:address/guidle:city'),
            )).strip(),
        ))

    def image(self, size: str) -> tuple[str, str] | tuple[None, None]:
        """ Returns the image url for the offer with the given size, together
        with the filename, or (None, None).

        """

        xpath = (
            f"guidle:offerDetail/"
            f"guidle:images/"
            f"guidle:image/"
            f"guidle:size[@label='{size}']"
        )

        images = self.find(f'({xpath})[1]')

        if not len(images):
            return None, None

        url = images[0].attrib['url']
        return url, url.rsplit('/', 1)[-1]

    def pdf(self) -> tuple[str, str] | tuple[None, None]:
        """ Returns the first attachment that is a pdf, together with
        the filename, or (None, None).

        """

        for attachment in self.find('guidle:offerDetail//guidle:attachment'):
            url = self.get('guidle:url', root=attachment)

            if not url.endswith('.pdf'):
                return None, None

            name = self.get('guidle:description', root=attachment)
            name = name.strip().split('\n')[0]

            return url, f'{name}.pdf'

        return None, None

    def tags(
        self,
        tagmap: Mapping[str, str] | None = None
    ) -> tuple[set[str], set[str]]:
        """ Returns a set of known and a set of unkonwn tags. """

        tag_elements = self.find(
            'guidle:classifications/'
            'guidle:classification[@type="PRIMARY"]/'
            'guidle:tag'
        )
        tags = {
            tag_name
            for tag in tag_elements
            if (tag_name := tag.get('subcategoryName') or tag.get('name'))
        }
        if tagmap:
            return (
                {tagmap[tag] for tag in tags if tag in tagmap},
                tags - tagmap.keys()
            )
        return tags, set()

    @cached_property
    def coordinates(self) -> RealCoordinates | None:
        lat = self.get('guidle:address/guidle:latitude', parser=float)
        lon = self.get('guidle:address/guidle:longitude', parser=float)
        if lat is not None and lon is not None:
            return Coordinates(lat, lon)
        return None

    def schedules(self) -> Iterator[GuidleScheduleDate]:
        for schedule in self.find('guidle:schedules/guidle:date'):
            yield GuidleScheduleDate(schedule)


class GuidleScheduleDate(GuidleBase):
    """ Represents a single schedule date of an offer. """

    def __init__(self, root: _Element) -> None:
        super().__init__(root)

        #  Parse start date, end date and recurrence
        start = self.get('guidle:startDate', parser=parse)
        end = self.get('guidle:endDate', parser=parse)
        recurrence = ''
        weekdays = self.get('guidle:weekdays/guidle:day', joiner=',')
        if weekdays:
            recurrence = f'RRULE:FREQ=WEEKLY;BYDAY={weekdays.upper()}'
        if end and not recurrence:
            if start != end:
                until = end + timedelta(days=1)
                recurrence = (
                    f'RRULE:FREQ=WEEKLY;'
                    f'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                    f'UNTIL={until:%Y%m%dT%H%M00Z}'
                )
                end = start
        else:
            if recurrence:
                if not end:
                    raise AssertionError('End date is required if recurrence '
                                         'is set for event')
                until = end + timedelta(days=1)
                recurrence += f';UNTIL={until:%Y%m%dT%H%M00Z}'
            end = start

        # Parse start and end times
        start_time = self.get(
            'guidle:startTime', parser=lambda x: parse(x, default=start)
        )
        end_time = self.get(
            'guidle:endTime', parser=lambda x: parse(x, default=end)
        )
        if start_time == end_time and recurrence:
            start_time = None
            end_time = None
        if start_time:
            start = start_time
        if end_time:
            end = end_time

        assert end is not None and start is not None
        if end <= start:
            end = end + timedelta(days=1) - timedelta(microseconds=1)

        # Add timezones
        if start:
            start = replace_timezone(start, self.timezone)
        if end:
            end = replace_timezone(end, self.timezone)

        self.start = start
        self.end = end
        self.recurrence = recurrence

    @cached_property
    def timezone(self) -> str:
        return 'Europe/Zurich'
