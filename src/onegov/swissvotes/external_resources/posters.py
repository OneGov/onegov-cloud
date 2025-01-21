from __future__ import annotations

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

    def get_object_id(self, url: str) -> str:
        raise NotImplementedError()

    def parse_xml(self, response: requests.Response) -> str:
        tree = lxml.etree.fromstring(response.content)
        element = tree.find("./field[@name='primaryMedia']/value")
        if element is None or not element.text:
            raise ValueError('No primary media found')
        return element.text

    def _fetch(
        self,
        bfs_number: Decimal,
        poster_urls: str | None,
        image_urls: dict[str, Any]
    ) -> tuple[dict[str, str], int, int, int, set[tuple[Decimal, str]]]:

        result: dict[str, str] = {}
        added = 0
        updated = 0
        removed = 0
        failed: set[tuple[Decimal, str]] = set()

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
                failed.add((bfs_number, self.get_object_id(url)))
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
        session: Session
    ) -> tuple[int, int, int, set[tuple[Decimal, str]]]:
        """

        Returns a dictionary with changed image urls as compared to the
        image_urls dictionary and if changed and how many added/updated.

        """

        updated_total = 0
        added_total = 0
        removed_total = 0
        failed_total = set()
        log.info('Fetching external resources.. (this takes a while)')
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
        self.base = 'https://www.emuseum.ch/objects/'

    def meta_data_url(self, url: str) -> str:
        object_id = self.get_object_id(url)
        return f'{self.base}{object_id}/xml'

    def get_object_id(self, url: str) -> str:
        return url.split(self.base)[-1].rstrip('/')


class BsPosters(Posters):
    """ Plakatsammlung Basel """

    def __init__(self, api_key: str) -> None:
        self.yea_attribute = 'posters_bs_yea'
        self.nay_attribute = 'posters_bs_nay'
        self.yea_img_attribute = 'posters_bs_yea_imgs'
        self.nay_img_attribute = 'posters_bs_nay_imgs'
        self.api_key = api_key
        self.headers = {}
        self.base = 'https://www.recherche-plakatsammlungbasel.ch/objects/'

    def meta_data_url(self, url: str) -> str:
        object_id = self.get_object_id(url)
        return f'{self.base}{object_id}/xml?key={self.api_key}'

    def get_object_id(self, url: str) -> str:
        return url.split(self.base)[-1].rstrip('/')


class SaPosters(Posters):
    """ Sozial Archiv Zürich """

    def __init__(self) -> None:
        self.yea_attribute = 'posters_sa_yea'
        self.nay_attribute = 'posters_sa_nay'
        self.yea_img_attribute = 'posters_sa_yea_imgs'
        self.nay_img_attribute = 'posters_sa_nay_imgs'
        self.headers = {}
        self.base = 'https://www.bild-video-ton.ch/bestand/objekt/'

    def meta_data_url(self, url: str) -> str:
        object_id = self.get_object_id(url)
        return f'https://swissvotes.sozialarchiv.ch/{object_id}'

    def get_object_id(self, url: str) -> str:
        return url.split(self.base)[-1].rstrip('/')
