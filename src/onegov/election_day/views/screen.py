from __future__ import annotations

from onegov.core.templates import PageTemplate
from onegov.core.widgets import inject_variables
from onegov.core.widgets import transform_structure
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Screen
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Screen,
    template='screen.pt',
    permission=MaybePublic
)
def view_screen(self: Screen, request: ElectionDayRequest) -> RenderData:
    """ Shows a screen. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    registry = request.app.config.screen_widget_registry
    widgets = registry.by_categories(self.screen_type.categories).values()
    layout: (
        ElectionLayout | ElectionCompoundLayout
        | ElectionCompoundPartLayout | VoteLayout
    )
    if self.type in ('simple_vote', 'complex_vote'):
        layout = VoteLayout(self.model, request)  # type:ignore[arg-type]
    elif self.type in ('majorz_election', 'proporz_election'):
        layout = ElectionLayout(self.model, request)  # type:ignore[arg-type]
    elif self.type == 'election_compound':
        layout = ElectionCompoundLayout(self.model, request)  # type:ignore
    elif self.type == 'election_compound_part':
        layout = ElectionCompoundPartLayout(self.model, request)  # type:ignore

    template = PageTemplate(transform_structure(widgets, self.structure))

    request.include('screen')

    if self.next:
        layout.custom_body_attributes['data-next'] = request.link(self.next)
        layout.custom_body_attributes['data-duration'] = (
            (self.duration or 20) * 1000)

    default = {
        'layout': layout,
        'template': template,
        'screen': self,
    }

    return inject_variables(widgets, layout, self.structure, default, False)


@ElectionDayApp.view(
    model=Screen,
    request_method='HEAD',
    permission=MaybePublic
)
def view_screen_head(self: Screen, request: ElectionDayRequest) -> None:
    """ Get the last modification date. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.json(
    model=Screen,
    name='json',
    permission=MaybePublic
)
def view_screen_json(self: Screen, request: ElectionDayRequest) -> JSON_ro:
    """ Get the last modification date. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return {
        'number': self.number,
        'description': self.description,
        'duration': self.duration,
        'next': self.next.number if self.next else None,
        'type': self.type,
        'model': (
            self.vote_id or self.election_id or self.election_compound_id
        ),
        'domain': self.domain,
        'domain_segment': self.domain_segment,
        'structure': self.structure,
        'css': self.css,
        'last_modified': (
            self.last_modified.isoformat() if self.last_modified else ''
        )
    }
