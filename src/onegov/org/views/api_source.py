""" Lets child organisations tell the parent organisation which of its topics
they link, see :mod:`onegov.org.api_source`. """
from onegov.api.models import ApiEndpointItem, ApiException
from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.org.api_source import accepts_api_link, add_api_link
from onegov.org.api_source import remove_api_link
from onegov.org.models import Topic
from webob.exc import HTTPBadRequest, HTTPForbidden, HTTPNotFound


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


def linked_topic(
    item: ApiEndpointItem[Any, Any],
    request: OrgRequest,
    url: Any
) -> Topic:

    if not isinstance(item.item, Topic):
        raise HTTPNotFound()

    if not isinstance(url, str) or not url:
        raise HTTPBadRequest()

    if not accepts_api_link(request.app.org, url):
        raise HTTPForbidden()

    return item.item


@OrgApp.json(
    model=ApiEndpointItem,
    name='links',
    request_method='POST',
    permission=Public
)
def register_api_link(
    self: ApiEndpointItem[Any, Any],
    request: OrgRequest
) -> dict[str, Any]:

    with ApiException.capture_exceptions():
        try:
            data = request.json_body
        except ValueError as exception:
            raise HTTPBadRequest() from exception

        if not isinstance(data, dict):
            raise HTTPBadRequest()

        topic = linked_topic(self, request, data.get('url'))
        title = data.get('title') or data['url']

        if not data.get('dry_run'):
            add_api_link(topic, data['url'], str(title))

        return {'url': data['url'], 'title': title}


@OrgApp.json(
    model=ApiEndpointItem,
    name='links',
    request_method='DELETE',
    permission=Public
)
def unregister_api_link(
    self: ApiEndpointItem[Any, Any],
    request: OrgRequest
) -> dict[str, Any]:

    with ApiException.capture_exceptions():
        url = request.GET.get('url')
        topic = linked_topic(self, request, url)
        remove_api_link(topic, url)  # type:ignore[arg-type]

        return {'url': url}
