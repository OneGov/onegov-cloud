from __future__ import annotations

from onegov.chat.collections import ChatCollection
from onegov.core.elements import Link, LinkGroup
from onegov.org.custom import get_global_tools as get_global_tools_base
from onegov.town6 import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.town6.request import TownRequest


def get_global_tools(request: TownRequest) -> Iterator[Link | LinkGroup]:
    for item in get_global_tools_base(request):

        classes = getattr(item, 'attrs', {}).get('class')
        if classes == {'login'} or classes == {'citizen-login'}:
            continue

        yield item

    if request.is_logged_in and request.app.org.meta.get(
        'enable_chat', 'disabled') == 'people_chat':
        chat_staff = request.app.org.meta.get('chat_staff', [])
        assert request.current_user is not None
        if request.current_user.id.hex in chat_staff:
            yield LinkGroup(_('Chats'), classes=('chats', ), links=(
                Link(
                    _('My Chats'), request.link(
                        request.app.org, name='chats'
                    ), attrs={'class': 'chats'}
                ),
                Link(
                    _('Archived Chats'),
                    request.class_link(
                        ChatCollection, {
                            'state': 'archived',
                        },
                        name='archive'
                    ),
                    attrs={
                        'class': ('chats-archive'),
                    }
                )
            ))
