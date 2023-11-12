from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.core.elements import Link, LinkGroup
from onegov.town6 import _


def get_global_tools(request):
    for item in get_global_tools_base(request):

        if getattr(item, 'attrs', {}).get('class') == {'login'}:
            continue

        yield item

    if request.is_logged_in:
        yield LinkGroup(_("Chats"), classes=('comments', ), links=(
            Link(
                _("My Chats"), request.link(
                    request.app.org, name='chats'
                ), attrs={'class': 'comments'}
            ),
            Link(
                _("Chats Archive"), request.link(
                    request.app.org, name='chats-archive'
                ), attrs={'class': 'comments'}
            ),
        )) 

