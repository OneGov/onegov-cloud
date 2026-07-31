from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.org import _, OrgApp
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest, PageMeta


@OrgApp.html(
    model=Organisation,
    name='topic-chart',
    template='topic_chart.pt',
    permission=Private
)
def view_topic_chart(
    self: Organisation,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:
    """ Shows the topic hierarchy (the information architecture) of the
    site as an interactive chart.

    """

    request.include('topic-chart')

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Topic chart'), '#')
    ]

    return {
        'title': _('Topic chart'),
        'layout': layout,
        'chart_url': request.link(
            self, name='topic-chart-json'
        ),
        'image_name': '{}-topic-chart'.format(
            normalize_for_url(self.name)
        )
    }


@OrgApp.json(
    model=Organisation,
    name='topic-chart-json',
    permission=Private,
    open_data=False
)
def view_topic_chart_json(
    self: Organisation,
    request: OrgRequest
) -> JSON_ro:
    """ Returns the topic hierarchy as a flat list of nodes, ready to be
    consumed by d3-org-chart.

    """

    nodes: list[JSON_ro] = [{
        'id': 'root',
        'parentId': None,
        'name': self.name,
        'url': request.link(self),
        'access': 'public',
        'published': True
    }]

    def add_nodes(pages: tuple[PageMeta, ...], parent_id: str) -> None:
        for page in pages:
            if page.type != 'topic':
                continue

            node_id = f'topic-{page.id}'
            nodes.append({
                'id': node_id,
                'parentId': parent_id,
                'name': page.title,
                'url': page.link(request),
                'access': page.access,
                'published': page.published
            })
            add_nodes(page.children, node_id)

    add_nodes(request.pages_tree, 'root')

    return {'nodes': nodes}
