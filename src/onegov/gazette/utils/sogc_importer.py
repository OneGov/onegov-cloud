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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SogcImporter:

    converters: dict[str, type[
        KK01 | KK02 | KK03 | KK04 | KK05
        | KK06 | KK07 | KK08 | KK09 | KK10
    ]]

    def __init__(self, session: 'Session', config: dict[str, str]):
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

    def get_publication_ids(self) -> list[str]:
        """ Returns the IDs of the publications we are interested in. Does not
        include the IDs of the publications which has been already imported
        previously.

        """
        result = {}

        page: int | None = 0
        while page is not None:
            response = get(
                f'{self.endpoint}/publications/xml',
                # FIXME: mypy is a bit too aggressive on the inference here
                #        this should actually work...
                params={  # type:ignore[arg-type]
                    'publicationStates': 'PUBLISHED',
                    'cantons': self.canton,
                    'subRubrics': self.subrubrics,
                    'pageRequest.page': page,
                    'pageRequest.size': 2000,
                },
                timeout=300
            )
            response.raise_for_status()

            root = etree.fromstring(response.text.encode('utf-8'))
            publications: dict[str, str] = {
                # FIXME: we should maybe also test that the text is not None
                p_no.text: p_id.text  # type:ignore[misc]
                for meta in root.findall('publication/meta')
                if (p_no := meta.find('publicationNumber')) is not None
                and (p_id := meta.find('id')) is not None
            }

            result.update(publications)
            page = page + 1 if publications else None

        existing_q = self.session.query(GazetteNotice.source)
        existing_q = existing_q.filter(GazetteNotice.source.isnot(None))
        existing = {source for source, in existing_q}

        return [
            id_ for source, id_ in result.items() if source not in existing
        ]

    def get_publication(self, identifier: str) -> None:
        """ Fetches a single publication and adds it as an official notice.

        """
        session = self.session

        response = get(
            f'{self.endpoint}/publications/{identifier}/xml',
            timeout=300
        )
        response.raise_for_status()
        response.encoding = 'utf-8'

        root = etree.fromstring(response.text.encode('utf-8'))
        subrubric_node = root.find('meta/subRubric')
        assert subrubric_node is not None
        subrubric = subrubric_node.text
        assert subrubric is not None
        converter = self.converters[subrubric](root)

        name = get_unique_notice_name(converter.title, session, GazetteNotice)
        author_date = converter.publication_date or None
        if author_date:
            author_date = standardize_date(author_date, 'UTC')
        expiry_date = converter.expiration_date or None
        if expiry_date:
            expiry_date = standardize_date(expiry_date, 'UTC')

        notice = GazetteNotice(  # type:ignore[misc]
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

    def __call__(self) -> int:
        publication_ids = self.get_publication_ids()
        for id_ in publication_ids:
            self.get_publication(id_)
        count = len(publication_ids)
        log.info(f"{count} notice(s) imported")
        return count
