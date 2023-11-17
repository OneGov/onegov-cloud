from onegov.core.elements import Link, LinkGroup
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.town6 import _


def get_global_tools(request):
    for item in get_global_tools_base(request):

        if getattr(item, 'attrs', {}).get('class') == {'login'}:
            continue

        yield item

    if request.is_logged_in and request.app.org.meta.get('enable_chat', False):
        chat_staff = request.app.org.meta.get('chat_staff', [])
        if request.current_user.id.hex in chat_staff:
            yield LinkGroup(_("Chats"), classes=('chats', ), links=(
                Link(
                    _("My Chats"), request.link(
                        request.app.org, name='chats'
                    ), attrs={'class': 'chats'}
                ),
            ))
