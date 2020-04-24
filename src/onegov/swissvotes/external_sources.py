from onegov.swissvotes.models import SwissVote
import requests
from xml.etree import ElementTree


def parse_xml(response):
    tree = ElementTree.fromstring(response.content)
    elem = tree.find("./field[@name='primaryMedia']/value")
    return elem.text if elem is not None else None


def get_obj_id(url):
    right = url.split('https://www.emuseum.ch/objects/')[-1]
    return right.split('/')[0]


def meta_data_url(obj_id, api_key):
    return f'https://www.emuseum.ch/objects/{obj_id}/xml?key={api_key}'


def fetch_changed(poster_urls, image_urls, api_key,):
    """Returns a dictionary with changed image urls as compared to the
    image_urls dictionary and if changed and how many added/updated.
    """
    new_urls = {}
    added = 0
    updated = 0
    failed = 0

    if not poster_urls:
        return new_urls, added, updated, failed
    if image_urls:
        assert isinstance(image_urls, dict)
    else:
        image_urls = {}

    for url in poster_urls.split(' '):
        api_url = meta_data_url(get_obj_id(url), api_key)
        try:
            resp = requests.get(api_url)
            if resp.status_code == 403:
                raise ValueError('403: Seems your api key is not valid')
            assert resp.status_code == 200
        except Exception as e:
            print(e.args[0])
            failed += 1
            continue
        try:
            img_url = parse_xml(resp)
            # eMuseum should deliver urls as https when they redirect anyway
            img_url = img_url.replace('http:', 'https:')
        except ElementTree.ParseError:
            failed += 1
            continue
        old_img_url = image_urls.get(url)
        if img_url and img_url != old_img_url:
            if not old_img_url:
                added += 1
            else:
                updated += 1
            new_urls[url] = img_url
    if new_urls:
        assert any((added != 0, updated != 0))
    return new_urls, added, updated, failed


def update_vote_dict(vote, attr, changed):
    attr_data = getattr(vote, attr)
    for k, v in changed.items():
        if k not in attr_data:
            attr_data[k] = v
        elif attr_data[k] != v:
            attr_data[k] = v
    setattr(vote, attr, attr_data)


def update_poster_urls(request):
    key = request.app.mfg_api_token
    assert key, "Provide an api key"
    updated_total = 0
    added_total = 0
    failed_total = 0
    for vote in request.session.query(SwissVote):
        changed, added, updated, failed = fetch_changed(
            vote.posters_yes, vote.posters_yes_imgs, key)
        updated_total += updated
        added_total += added
        failed_total += failed
        if changed:
            if isinstance(vote.posters_yes_imgs, dict):
                update_vote_dict(vote, 'posters_yes_imgs', changed)
            else:
                vote.posters_yes_imgs = changed

        changed, added, updated, failed = fetch_changed(
            vote.posters_no, vote.posters_no_imgs, key)
        updated_total += updated
        added_total += added
        failed_total += failed
        if changed:
            if isinstance(vote.posters_no_imgs, dict):
                update_vote_dict(vote, 'posters_no_imgs', changed)
            else:
                vote.posters_no_imgs = changed

    return added_total, updated_total, failed_total
