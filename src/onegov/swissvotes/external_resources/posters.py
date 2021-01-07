from onegov.swissvotes import log
from onegov.swissvotes.models import SwissVote
from requests import get
from xml.etree import ElementTree


class ExternalSource():

    def __init__(self):
        self.base_path = None
        self.yea_attribute = None
        self.nay_attribute = None
        self.yea_img_attribute = None
        self.nay_img_attribute = None

    def meta_data_url(self, url):
        raise NotImplementedError()

    def parse_xml(self, response):
        tree = ElementTree.fromstring(response.content)
        element = tree.find("./field[@name='primaryMedia']/value")
        if element is None or not element.text:
            raise ValueError('No primary media found')
        return element.text

    def _fetch(self, bfs_number, poster_urls, image_urls):
        result = {}
        added = 0
        updated = 0
        removed = 0
        failed = set()

        if not poster_urls:
            return result, added, updated, removed, failed

        image_urls = image_urls if isinstance(image_urls, dict) else {}

        for url in poster_urls.split(' '):
            meta_data_url = self.meta_data_url(url)
            try:
                response = get(meta_data_url)
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

        removed = len(set(image_urls.keys()) - set(result.keys()))
        return result, added, updated, removed, failed

    def fetch(self, session):
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


class MfgPosters(ExternalSource):

    def __init__(self, api_key):
        self.yea_attribute = 'posters_mfg_yea'
        self.nay_attribute = 'posters_mfg_nay'
        self.yea_img_attribute = 'posters_mfg_yea_imgs'
        self.nay_img_attribute = 'posters_mfg_nay_imgs'
        self.api_key = api_key

    def meta_data_url(self, url):
        base = 'https://www.emuseum.ch/objects/'
        object_id = url.split(base)[-1].rstrip('/')
        return f'{base}{object_id}/xml?key={self.api_key}'


class SaPosters(ExternalSource):

    def __init__(self):
        self.yea_attribute = 'posters_sa_yea'
        self.nay_attribute = 'posters_sa_nay'
        self.yea_img_attribute = 'posters_sa_yea_imgs'
        self.nay_img_attribute = 'posters_sa_nay_imgs'

    def meta_data_url(self, url):
        base = 'https://www.bild-video-ton.ch/bestand/objekt/'
        object_id = url.split(base)[-1].rstrip('/')
        return f'https://swissvotes.sozialarchiv.ch/{object_id}'
