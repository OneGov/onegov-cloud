from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.org.models import Organisation
from onegov.core.elements import Link


def get_global_tools(request):
    for item in get_global_tools_base(request):
        if getattr(item, 'title', None) == 'Management':
            item.links.append(Link(
                text=_("Hidden contents"),
                url=request.class_link(Organisation, name='view-hidden'),
                attrs={"class": "hidden-contents"}
            ))
        yield item


def get_top_navigation(request):
    yield Link(
        text=_("People"),
        url=request.class_link(ExtendedPersonCollection)
    )
    yield Link(
        text=_("Agencies"),
        url=request.class_link(ExtendedAgencyCollection)
    )
