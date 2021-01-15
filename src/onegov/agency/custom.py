from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.core.elements import Link
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.org.models import Organisation
from onegov.user import UserGroupCollection


def get_global_tools(request):
    for item in get_global_tools_base(request):
        title = getattr(item, 'title', None)

        if title == 'Management':
            if request.is_admin:
                item.links.append(Link(
                    text=_('User groups'),
                    url=request.class_link(UserGroupCollection),
                    attrs={'class': 'users'}
                ))
            item.links.append(Link(
                text=_('Hidden contents'),
                url=request.class_link(Organisation, name='view-hidden'),
                attrs={'class': 'hidden-contents'}
            ))

        if title == 'Tickets':
            item.classes = ('tickets', )
            for link in item.links:
                if 'with-count' in link.attrs['class']:
                    link.attrs['class'].remove('with-count')

        yield item


def get_top_navigation(request):
    yield Link(
        text=_('People'),
        url=request.class_link(ExtendedPersonCollection)
    )
    yield Link(
        text=_('Agencies'),
        url=request.class_link(ExtendedAgencyCollection)
    )
