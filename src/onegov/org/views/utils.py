from __future__ import annotations

from functools import lru_cache


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


# FIXME: I think these would make more sense as cached_property on OrgRequest
@lru_cache(maxsize=1)
def show_tags(request: OrgRequest) -> bool:
    return request.app.org.event_filter_type in ('tags', 'tags_and_filters')


@lru_cache(maxsize=1)
def show_filters(request: OrgRequest) -> bool:
    return request.app.org.event_filter_type in ('filters', 'tags_and_filters')
