from lxml import etree
from onegov.chat import MessageCollection
from onegov.gazette import _
from onegov.gazette import log
from onegov.gazette.models import GazetteNotice
from onegov.gazette.utils.sogc_converter import KK01
from onegov.gazette.utils.sogc_converter import KK02
from onegov.gazette.utils.sogc_converter import KK03
from onegov.gazette.utils.sogc_converter import KK04
from onegov.gazette.utils.sogc_converter import KK05
from onegov.gazette.utils.sogc_converter import KK06
from onegov.gazette.utils.sogc_converter import KK07
from onegov.gazette.utils.sogc_converter import KK08
from onegov.gazette.utils.sogc_converter import KK09
from onegov.gazette.utils.sogc_converter import KK10
from onegov.notice.collections import get_unique_notice_name
from requests import get
from sedate import standardize_date
from uuid import uuid4


class SogcImporter(object):

    def __init__(self, session, config):
        self.session = session
        self.endpoint = config['endpoint'].rstrip('/')
        self.canton = config['canton']
        self.category = config['category']
        self.organization = config['organization']
        self.converters = {
            'KK01': KK01,
            'KK02': KK02,
            'KK03': KK03,
            'KK04': KK04,
            'KK05': KK05,
            'KK06': KK06,
            'KK07': KK07,
            'KK08': KK08,
            'KK09': KK09,
            'KK10': KK10,
        }
        self.subrubrics = list(self.converters.keys())

    def get_publication_ids(self):
        """ Returns the IDs of the publications we are interested in. Does not
        include the IDs of the publications which has been already imported
        previously.

        """
        result = {}

        page = 0
        while page is not None:
            response = get(
                f'{self.endpoint}/publications/xml',
                params={
                    'publicationStates': 'PUBLISHED',
                    'cantons': self.canton,
                    'subRubrics': self.subrubrics,
                    'pageRequest.page': page,
                    'pageRequest.size': 2000,
                }
            )
            response.raise_for_status()

            root = etree.fromstring(response.text.encode('utf-8'))
            publications = {
                meta.find('publicationNumber').text: meta.find('id').text
                for meta in root.findall('publication/meta')
            }

            result.update(publications)
            page = page + 1 if publications else None

        existing = self.session.query(GazetteNotice.source)
        existing = existing.filter(GazetteNotice.source.isnot(None))
        existing = set([result.source for result in existing])

        return [
            id_ for source, id_ in result.items() if source not in existing
        ]

    def get_publication(self, identifier):
        """ Fetches a single publication and adds it as an official notice.

        """
        session = self.session

        response = get(f'{self.endpoint}/publications/{identifier}/xml')
        response.raise_for_status()
        response.encoding = 'utf-8'

        root = etree.fromstring(response.text.encode('utf-8'))
        subrubric = root.find('meta/subRubric').text
        converter = self.converters[subrubric](root)

        name = get_unique_notice_name(converter.title, session, GazetteNotice)
        author_date = converter.publication_date or None
        if author_date:
            author_date = standardize_date(author_date, 'UTC')
        expiry_date = converter.expiration_date or None
        if expiry_date:
            expiry_date = standardize_date(expiry_date, 'UTC')

        notice = GazetteNotice(
            id=uuid4(),
            name=name,
            state='imported',
            source=converter.source,
            title=converter.title,
            text=converter.text,
            organization_id=self.organization,
            category_id=self.category,
            issues=converter.issues(session),
            author_date=author_date,
            expiry_date=expiry_date
        )
        notice.apply_meta(session)
        session.add(notice)
        session.flush()

        MessageCollection(session, type='gazette_notice').add(
            channel_id=str(notice.id),
            meta={'event': _("imported")}
        )

    def __call__(self):
        publication_ids = self.get_publication_ids()
        for id_ in publication_ids:
            self.get_publication(id_)
        count = len(publication_ids)
        log.info(f"{count} notice(s) imported")
        return count
