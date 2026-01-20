""" The onegov winterthur occurrence views. """
from __future__ import annotations

from morepath.request import Response

from onegov.core.security import Public
from onegov.event import OccurrenceCollection, EventCollection
from onegov.winterthur import WinterthurApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.view(model=OccurrenceCollection, name='xml', permission=Public)
def xml_export_all_events(
    self: OccurrenceCollection,
    request: WinterthurRequest
) -> Response:
    """
    Returns events as xml in Anthrazit format.
    This view was requested by Winterthur for their mobile app that displays
    the events provided by this xml view.

    Url for xml view: ../events/xml

    """
    collection = EventCollection(request.session)
    return Response(
        collection.as_anthrazit_xml(request),
        content_type='text/xml',
        content_disposition='inline; filename=events.xml'
    )
