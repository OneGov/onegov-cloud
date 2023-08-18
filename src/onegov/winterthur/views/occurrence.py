""" The onegov winterthur occurrence views. """

from morepath.request import Response

from onegov.core.security import Public
from onegov.event import OccurrenceCollection
from onegov.winterthur import WinterthurApp


@WinterthurApp.view(model=OccurrenceCollection, name='xml', permission=Public)
def xml_export_all_occurrences(self, request):
    """
    Returns events as xml in Anthrazit format.
    This view was requested by Winterthur for their mobile app that displays
    the events provided by this xml view.

    Url for xml view: ../events/xml

    """
    collection = OccurrenceCollection(request.session)
    return Response(
        collection.as_anthrazit_xml(),
        content_type='text/xml',
        content_disposition='inline; filename=occurrences.xml'
    )
