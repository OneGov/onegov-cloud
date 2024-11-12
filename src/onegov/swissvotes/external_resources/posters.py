import lxml.etree
import requests
from onegov.swissvotes import log
from onegov.swissvotes.models import SwissVote


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from decimal import Decimal
    from sqlalchemy.orm import Session


class Posters:

    # NOTE: These need to be set by the subclass
    yea_attribute: str
    nay_attribute: str
    yea_img_attribute: str
    nay_img_attribute: str
    headers: dict[str, str]

    def meta_data_url(self, url: str) -> str:
        raise NotImplementedError()

    def parse_xml(self, response: requests.Response) -> str:
        tree = lxml.etree.fromstring(response.content)
        element = tree.find("./field[@name='primaryMedia']/value")
        if element is None or not element.text:
            raise ValueError('No primary media found')
        return element.text

    def _fetch(
        self,
        bfs_number: 'Decimal',
        poster_urls: str | None,
        image_urls: dict[str, Any]
    ) -> tuple[dict[str, str], int, int, int, set['Decimal']]:

        result: dict[str, str] = {}
        added = 0
        updated = 0
        removed = 0
        failed: set[Decimal] = set()

        if not poster_urls:
            removed = len(image_urls)
            return result, added, updated, removed, failed

        image_urls = image_urls if isinstance(image_urls, dict) else {}

        for url in poster_urls.split(' '):
            if not url:
                continue
            meta_data_url = self.meta_data_url(url)
            try:
                response = requests.get(
                    meta_data_url,
                    headers=self.headers,
                    timeout=60
                )
                response.raise_for_status()
                image_url = self.parse_xml(response)
                image_url = image_url.replace('http:', 'https:')
            except Exception as exception:
                log.warning(
                    f'Getting external resource {bfs_number} {url} failed: '
                    f'{exception}'
                )
                failed.add(bfs_number)
            else:
                result[url] = image_url
                old_image_url = image_urls.get(url)
                if old_image_url:
                    if image_url != old_image_url:
                        updated += 1
                else:
                    added += 1

        if not failed:
            removed = len(set(image_urls.keys()) - set(result.keys()))

        return result, added, updated, removed, failed

    def fetch(
        self,
        session: 'Session'
    ) -> tuple[int, int, int, set['Decimal']]:
        """

        Returns a dictionary with changed image urls as compared to the
        image_urls dictionary and if changed and how many added/updated.

        """

        updated_total = 0
        added_total = 0
        removed_total = 0
        failed_total = set()
        for vote in session.query(SwissVote):
            result, added, updated, removed, failed = self._fetch(
                vote.bfs_number,
                getattr(vote, self.yea_attribute),
                getattr(vote, self.yea_img_attribute),
            )
            updated_total += updated
            added_total += added
            removed_total += removed
            failed_total |= failed
            if not failed:
                setattr(vote, self.yea_img_attribute, result)

            result, added, updated, removed, failed = self._fetch(
                vote.bfs_number,
                getattr(vote, self.nay_attribute),
                getattr(vote, self.nay_img_attribute),
            )
            updated_total += updated
            added_total += added
            removed_total += removed
            failed_total |= failed
            if not failed:
                setattr(vote, self.nay_img_attribute, result)

        return added_total, updated_total, removed_total, failed_total


class MfgPosters(Posters):

    def __init__(self, api_key: str) -> None:
        self.yea_attribute = 'posters_mfg_yea'
        self.nay_attribute = 'posters_mfg_nay'
        self.yea_img_attribute = 'posters_mfg_yea_imgs'
        self.nay_img_attribute = 'posters_mfg_nay_imgs'
        self.headers = {'X-API-KEY': api_key}

    def meta_data_url(self, url: str) -> str:
        base = 'https://www.emuseum.ch/objects/'
        object_id = url.split(base)[-1].rstrip('/')
        return f'{base}{object_id}/xml'


class SaPosters(Posters):

    def __init__(self) -> None:
        self.yea_attribute = 'posters_sa_yea'
        self.nay_attribute = 'posters_sa_nay'
        self.yea_img_attribute = 'posters_sa_yea_imgs'
        self.nay_img_attribute = 'posters_sa_nay_imgs'
        self.headers = {}

    def meta_data_url(self, url: str) -> str:
        base = 'https://www.bild-video-ton.ch/bestand/objekt/'
        object_id = url.split(base)[-1].rstrip('/')
        return f'https://swissvotes.sozialarchiv.ch/{object_id}'
