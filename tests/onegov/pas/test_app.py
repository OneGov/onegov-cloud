from onegov.pas.custom import get_global_tools
from onegov.pas.custom import get_top_navigation
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.utils import Bunch


class DummyRequest():
    is_logged_in = False
    is_manager = False
    is_admin = False
    current_user = Bunch(id=Bunch(hex='abcd'))
    path = ''
    url = ''

    def class_link(self, cls, name=''):
        return f'{cls.__name__}/{name}'

    def link(self, target, name=None):
        return f"{target.__class__.__name__}/{name}"

    def transform(self, url):
        return url

    def include(self, asset):
        pass

    def exclude_invisible(self, items):
        return []


def test_app_custom(pas_app):
    def as_text(items):
        result = []
        for item in items:
            if isinstance(item, Link):
                result.append(item.text)
            if isinstance(item, LinkGroup):
                result.append({item.title: as_text(item.links)})
        return result

    request = DummyRequest()
    request.app = pas_app

    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == []

    request.is_logged_in = True
    request.current_username = 'Peter'
    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == [{'Peter': ['Logout']}]

    request.is_manager = True
    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == [{'Peter': ['Logout']}]

    request.is_admin = True
    assert as_text(get_top_navigation(request)) == []
    assert as_text(get_global_tools(request)) == [
        {'Peter': ['Logout']},
        {'Management': [
            'Attendences', 'Parliamentarians', 'Commissions',
            'Legislative periods', 'Parliamentary groups', 'Parties',
            'Users', 'Settings'
        ]}
    ]
