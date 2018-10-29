from bleach.sanitizer import Cleaner
from cached_property import cached_property
from datetime import timedelta
from dateutil.parser import parse
from onegov.gis import Coordinates
from sedate import replace_timezone


class GuidleBase(object):
    """ Base class for parsing guidle exports containing general helpers. """

    def __init__(self, root):
        self.root = root
        self.nsmap = {'guidle': 'http://www.guidle.com'}
        self.cleaner = Cleaner(
            tags=[],
            attributes={},
            styles=[],
            strip=True,
            filters=[]
        )

    def find(self, path, root=None):
        """ Gets the elements with the given path. """

        root = root if root is not None else self.root
        return root.xpath(path, namespaces=self.nsmap) or []

    def get(self, path, root=None, joiner=' ', parser=None):
        """ Returns the text of the elements with the given path.

        Allows to specifiy a joining character and optionally a parser. If no
        parser is given, the text is HTML-cleaned.

        """

        result = joiner.join([
            (element.text or '').strip() for element in self.find(path, root)
        ]).strip()
        if parser and result:
            result = parser(result)
        else:
            result = self.cleaner.clean(result or '')
        return result

    def join(self, texts, joiner=', '):
        """ Joins a set of text, skips duplicate and empty texts. """

        return joiner.join((
            text for index, text in enumerate(texts)
            if text and text not in texts[index + 1:]
        ))


class GuidleExportData(GuidleBase):
    """ Represents a whole guidle export. """

    def offers(self):
        for offer in self.find('.//guidle:offer'):
            yield GuidleOffer(offer)


class GuidleOffer(GuidleBase):
    """ Represents a single offer containing some description and dates. """

    @cached_property
    def uid(self):
        return self.root.get('id')

    @cached_property
    def last_update(self):
        return self.get('guidle:lastUpdateDate')

    @cached_property
    def title(self):
        title = self.get('guidle:offerDetail/guidle:title')

        # titles are rendered as unsafe html downstream, so we can
        # losen the rules one tiny bit here.

        # we'll still have '&gt,' and '&lt;', but those are probably
        # used very rarely in a title, so we can ignore that
        title = title.replace('&amp;', '&')

        return title

    @cached_property
    def description(self):
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
            self.get('guidle:offerDetail/guidle:priceInformation'),
            self.get('guidle:offerDetail/guidle:ticketingUrl')
        ), '\n\n')

    @cached_property
    def organizer(self):
        return self.join((
            self.get('guidle:contact/guidle:company'),
            self.get('guidle:contact/guidle:name'),
            self.get('guidle:contact/guidle:email'),
            self.get('guidle:contact/guidle:telephone_1'),
        ))

    @cached_property
    def location(self):
        return self.join((
            self.get('guidle:address/guidle:company'),
            self.get('guidle:address/guidle:street'),
            ' '.join((
                self.get('guidle:address/guidle:zip'),
                self.get('guidle:address/guidle:city'),
            )).strip(),
        ))

    def image_url(self, size):
        """ Returns the image url for the offer with the given size or None.

        """

        xpath = (
            f"guidle:offerDetail/"
            f"guidle:images/"
            f"guidle:image/"
            f"guidle:size[@label='{size}']"
        )

        images = self.find(f"({xpath})[1]")

        if not len(images):
            return None

        return images[0].attrib['url']

    def tags(self, tagmap=None):
        """ Returns a set of known and a set of unkonwn tags. """

        tags = self.find(
            'guidle:classifications/'
            'guidle:classification[@type="PRIMARY"]/'
            'guidle:tag'
        )
        tags = [tag.get('subcategoryName') or tag.get('name') for tag in tags]
        tags = set([tag for tag in tags if tag])
        if tagmap:
            return (
                {tagmap[tag] for tag in tags if tag in tagmap},
                tags - tagmap.keys()
            )
        return tags, set()

    @cached_property
    def coordinates(self):
        lat = self.get('guidle:address/guidle:latitude', parser=float)
        lon = self.get('guidle:address/guidle:longitude', parser=float)
        if lat and lon:
            return Coordinates(lat, lon)

    def schedules(self):
        for schedule in self.find('guidle:schedules/guidle:date'):
            yield GuidleScheduleDate(schedule)


class GuidleScheduleDate(GuidleBase):
    """ Represents a single schedule date of an offer. """

    def __init__(self, root):
        super(GuidleScheduleDate, self).__init__(root)

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
                    f'UNTIL={until:%Y%m%dT%H%MZ}'
                )
                end = start
        else:
            if recurrence:
                until = end + timedelta(days=1)
                recurrence += f';UNTIL={until:%Y%m%dT%H%MZ}'
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
    def timezone(self):
        return 'Europe/Zurich'
