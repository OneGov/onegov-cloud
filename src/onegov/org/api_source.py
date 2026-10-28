""" Links topics of this instance to topics of another OneGov instance.

The source instance is configured through its API url in the settings
(:attr:`onegov.org.models.Organisation.api_source_url`). Topics with the
'api' trait store the id of the linked source topic and get their title,
lead, text and sidebar contents from the API of the source instance.

FIXME: This is a demo! The linked topics are synced on every page view
(see :func:`onegov.org.app.sync_api_topics_tween_factory`), which is not
something we would want to do in production.

"""
import niquests

from onegov.core.html import sanitize_html
from onegov.org import log
from urllib.parse import urljoin, urlsplit, urlunsplit


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import Organisation, Topic
    from sqlalchemy.orm import Session


#: The local debug server only handles one request at a time. A request
#: to the API of the same server would therefore block forever. To avoid
#: this, `onegov-server` starts a second worker on this port in debug mode
#: (port + 10, since 8081 is used by smtp4dev in our docker-compose setup),
#: which we use for all server-side API requests to the local server.
DEMO_API_WORKER_PORTS = {8080: 8090}

#: Marks the source topic as unavailable (not public anymore or deleted)
UNAVAILABLE = None


class ApiSourceError(Exception):
    """ Raised if the source API could not be reached. """


def api_source_base_url(api_url: str) -> str:
    """ Returns the base url of the source instance for the given API url.

    https://onegov.govikon.ch/api/
    -> https://onegov.govikon.ch/

    """
    base = api_url.rstrip('/')
    if base.endswith('/api'):
        base = base[:-len('/api')]
    return base + '/'


def api_topic_url(api_url: str, topic_id: int) -> str:
    return urljoin(api_url.rstrip('/') + '/', f'topics/{topic_id}')


def api_topic_edit_url(api_url: str, topic_id: int) -> str:
    return urljoin(
        api_source_base_url(api_url), f'editor/edit/page/{topic_id}')


def server_side_url(url: str) -> str:
    """ Rewrites urls pointing to the local debug server to the second
    worker, see :attr:`DEMO_API_WORKER_PORTS`.

    """
    parts = urlsplit(url)
    if parts.hostname in ('127.0.0.1', 'localhost'):
        port = DEMO_API_WORKER_PORTS.get(parts.port or 80)
        if port is not None:
            parts = parts._replace(netloc=f'{parts.hostname}:{port}')
    return urlunsplit(parts)


def public_url(url: str) -> str:
    """ Reverts :func:`server_side_url` for links shown to the user. """
    parts = urlsplit(url)
    if parts.hostname in ('127.0.0.1', 'localhost'):
        for public, worker in DEMO_API_WORKER_PORTS.items():
            if parts.port == worker:
                parts = parts._replace(netloc=f'{parts.hostname}:{public}')
    return urlunsplit(parts)


def fetch_api_topic(api_url: str, topic_id: int) -> dict[str, Any] | None:
    """ Fetches the data of the given topic from the source API.

    Returns :attr:`UNAVAILABLE` if the topic is not publicly available
    anymore. Raises :class:`ApiSourceError` if the API can't be reached.

    """
    url = server_side_url(api_topic_url(api_url, topic_id))
    try:
        response = niquests.get(
            url,
            headers={'Accept': 'application/vnd.collection+json'},
            timeout=10
        )
    except niquests.RequestException as exception:
        raise ApiSourceError(str(exception)) from exception

    if response.status_code in (400, 404):
        return UNAVAILABLE

    if response.status_code != 200:
        raise ApiSourceError(f'{url} returned {response.status_code}')

    try:
        items = response.json()['collection']['items']
    except (ValueError, KeyError, TypeError) as exception:
        raise ApiSourceError(f'{url} returned invalid data') from exception

    if not items:
        return UNAVAILABLE

    item = items[0]
    data = {d['name']: d['value'] for d in item.get('data', ())}
    links = {
        link['rel']: link['href'] for link in item.get('links', ())
    }

    # an empty item is returned if the topic is invisible, the text is
    # missing for topics which are not public (mTAN)
    if not data.get('title') or 'text' not in data:
        return UNAVAILABLE

    data['html_url'] = public_url(links['html']) if links.get('html') else None
    return data


def absolute_links(
    links: list[list[str | None]] | None,
    base_url: str
) -> list[list[str | None]]:
    """ Turns relative sidebar links of the source into absolute ones.

    Paths like '/topics/x' are relative to the source instance, not to the
    host, as the instance might be hosted in a sub path (e.g. locally).

    """
    def absolute(url: str | None) -> str | None:
        if not url or urlsplit(url).scheme:
            return url
        return urljoin(base_url, url.lstrip('/'))

    return [[text, absolute(url)] for text, url in (links or ())]


def apply_api_topic(
    topic: Topic,
    api_url: str,
    data: dict[str, Any] | None
) -> None:
    """ Applies the fetched data to the given topic. Only writes values
    which have changed, to avoid needless updates (and reindexing).

    """

    def update(name: str, value: Any, target: dict[str, Any]) -> None:
        if target.get(name) != value:
            target[name] = value

    if data is UNAVAILABLE:
        if not topic.api_unavailable:
            # hide the topic from the public (and the public search)
            topic.api_unavailable = True
            topic.api_previous_access = topic.access
            topic.access = 'private'
        return

    if topic.api_unavailable:
        topic.api_unavailable = False
        topic.access = topic.api_previous_access or 'public'
        topic.api_previous_access = None

    base_url = api_source_base_url(api_url)
    text = sanitize_html(data.get('text') or '')
    content = dict(topic.content or {})
    update('lead', data.get('lead') or None, content)
    update('text', str(text), content)
    update('contact', data.get('contact') or None, content)
    update('inherit_contact', False, content)
    update('sidepanel_links', absolute_links(
        data.get('sidepanel_links'), base_url), content)
    update('sidepanel_contact', absolute_links(
        data.get('sidepanel_contact'), base_url), content)

    if content != topic.content:
        topic.content = content
        # clear cached contact
        topic.__dict__.pop('contact_html', None)

    update('api_html_url', data.get('html_url'), topic.meta)
    update('api_source_title', data['title'], topic.meta)

    if topic.api_use_source_title and topic.title != data['title']:
        topic.title = data['title']


def sync_api_topic(topic: Topic, api_url: str) -> None:
    try:
        data = fetch_api_topic(api_url, topic.api_topic_id)  # type:ignore
    except ApiSourceError as exception:
        # keep the last known state if the source can't be reached
        log.warning(f'Could not sync API topic {topic.id}: {exception}')
        return

    apply_api_topic(topic, api_url, data)


def api_topics(session: Session) -> list[Topic]:
    from onegov.org.models import Topic
    return (
        session.query(Topic)
        .filter(Topic.meta['trait'].astext == 'api')
        .all()
    )


def sync_api_topics(session: Session, org: Organisation) -> None:
    """ Syncs all API topics of the current instance. """
    if not org.api_source_url:
        return

    for topic in api_topics(session):
        if topic.api_topic_id:
            sync_api_topic(topic, org.api_source_url)
