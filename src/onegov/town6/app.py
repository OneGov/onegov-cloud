from __future__ import annotations

from datetime import datetime

import pytz
from sedate import replace_timezone

from onegov.api import ApiApp
from onegov.core import utils
from onegov.core.i18n import default_locale_negotiator
from onegov.core.templates import render_template
from onegov.core.utils import module_path
from onegov.foundation6.integration import FoundationApp
from onegov.org.app import OrgApp
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.town6.api import (
    EventApiEndpoint, NewsApiEndpoint, TopicApiEndpoint)
from onegov.town6.custom import get_global_tools
from onegov.town6.initial_content import create_new_organisation
from onegov.town6.theme import TownTheme
from webob import Response


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from onegov.api import ApiEndpoint
    from onegov.core.types import RenderData
    from onegov.org.exceptions import MTANAccessLimitExceeded
    from onegov.org.models import Organisation
    from onegov.town6.request import TownRequest


class TownApp(OrgApp, FoundationApp, ApiApp):

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = True,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:
        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )

    @property
    def font_family(self) -> str | None:
        return self.theme_options.get('body-font-family-ui')

    def chat_open(self, request: TownRequest) -> bool:
        if not request.app.org.specific_opening_hours:
            return True
        opening_hours = request.app.org.opening_hours_chat
        tz = pytz.timezone('Europe/Zurich')
        now = datetime.now(tz=tz)
        if opening_hours:
            for day, start, end in opening_hours:
                if str(now.weekday()) == day:
                    open = replace_timezone(
                        datetime(now.year, now.month, now.day,
                                 int(start.split(':')[0]),
                                 int(start.split(':')[1])), tz)
                    close = replace_timezone(
                        datetime(now.year, now.month, now.day,
                                 int(end.split(':')[0]),
                                 int(end.split(':')[1])), tz)
                    if now > open and now < close:
                        return True
        return False


@TownApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@TownApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@TownApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@TownApp.template_variables()
def get_template_variables(request: TownRequest) -> RenderData:
    return {
        'global_tools': tuple(get_global_tools(request))
    }


@TownApp.setting(section='core', name='theme')
def get_theme() -> TownTheme:
    return TownTheme()


@TownApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH'}


@TownApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        module_path('onegov.town6', 'locale'),
        *get_org_i18n_localedirs()
    ]


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@TownApp.setting(section='i18n', name='locale_negotiator')
def get_locale_negotiator(
) -> Callable[[Sequence[str], TownRequest], str | None]:
    def locale_negotiator(
        locales: Sequence[str],
        request: TownRequest
    ) -> str | None:
        if request.app.org:
            locales = request.app.org.locales or get_i18n_default_locale()

            if isinstance(locales, str):
                locales = (locales, )

            return default_locale_negotiator(locales, request) or locales[0]
        else:
            return default_locale_negotiator(locales, request)
    return locale_negotiator


@TownApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[TownApp, str], Organisation]:
    return create_new_organisation


@TownApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles() -> tuple[str, ...]:
    return ('admin', 'editor')


@TownApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles() -> tuple[str, ...]:
    return ('admin', 'editor', 'supporter')


@TownApp.setting(section='org', name='require_complete_userprofile')
def get_require_complete_userprofile() -> bool:
    return False


@TownApp.setting(section='org', name='is_complete_userprofile')
def get_is_complete_userprofile_handler(
) -> Callable[[TownRequest, str], bool]:
    def is_complete_userprofile(request: TownRequest, username: str) -> bool:
        return True

    return is_complete_userprofile


@TownApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget() -> None:
    return None


@TownApp.setting(section='org', name='default_event_search_widget')
def get_default_event_search_widget() -> None:
    return None


@TownApp.setting(section='org', name='public_ticket_messages')
def get_public_ticket_messages() -> tuple[str, ...]:
    """ Returns a list of message types which are availble on the ticket
    status page, visible to anyone that knows the unguessable url.

    """

    # do *not* add ticket_note here, those are private!
    return (
        'directory',
        'event',
        'payment',
        'reservation',
        'submission',
        'ticket',
        'ticket_chat',
    )


@TownApp.setting(section='org', name='disabled_extensions')
def get_disabled_extensions() -> tuple[str, ...]:
    return ()


@TownApp.setting(section='org', name='render_mtan_access_limit_exceeded')
def get_render_mtan_access_limit_exceeded(
) -> Callable[[MTANAccessLimitExceeded, TownRequest], Response]:

    # circular import
    from onegov.town6.layout import DefaultLayout

    def render_mtan_access_limit_exceeded(
        self: MTANAccessLimitExceeded,
        request: TownRequest
    ) -> Response:
        return Response(
            render_template('mtan_access_limit_exceeded.pt', request, {
                'layout': DefaultLayout(self, request),
                'title': self.title,
            }),
            status=423
        )
    return render_mtan_access_limit_exceeded


@TownApp.setting(section='api', name='endpoints')
def get_api_endpoints() -> list[type[ApiEndpoint[Any]]]:
    return [
        EventApiEndpoint,
        NewsApiEndpoint,
        TopicApiEndpoint,
    ]


@TownApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@TownApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@TownApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@TownApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield 'global.js'
    yield 'polyfills.js'
    yield 'jquery.datetimepicker.css'
    yield 'locale.js'
    yield 'modernizr.js'
    yield 'clipboard.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'react.js'
    yield 'react-dom.js'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'typeahead.jsx'
    yield 'many.jsx'
    yield 'pay'
    yield 'moment.js'
    yield 'moment.de-ch.js'
    yield 'moment.fr-ch.js'
    yield 'jquery.datetimepicker.js'
    yield 'jquery.mousewheel.js'
    yield 'jquery.popupoverlay.js'
    yield 'jquery.load.js'
    yield 'videoframe.js'
    yield 'datetimepicker.js'
    yield 'url.js'
    yield 'date-range-selector.js'
    yield 'lazyalttext.js'
    yield 'lazysizes.js'
    yield 'common.js'
    yield '_blank.js'
    yield 'homepage_video_or_slider.js'
    yield 'file-table-row-toggler.js'
    yield 'animate.js'
    yield 'forms.js'
    yield 'internal_link_check.js'
    yield 'tickets.js'
    yield 'items_selectable.js'
    yield 'aos.js'
    yield 'aos-init.js'
    yield 'aos.css'
    yield 'notifications.js'
    yield 'sidebar_mobile.js'
    yield 'sidebar_fixed.js'
    yield 'ResizeSensor.js'
    yield 'theia-sticky-sidebar.js'
    yield 'chosen_select_hierarchy.js'
    yield 'iframe_request_parameters.js'


@TownApp.webasset('editor')
def get_editor_asset() -> Iterator[str]:
    yield 'bufferbuttons.js'
    yield 'definedlinks.js'
    yield 'filemanager.js'
    yield 'imagemanager.js'
    yield 'table.js'
    yield 'redactor.de.js'
    yield 'redactor.fr.js'
    yield 'redactor.it.js'
    yield 'input_with_button.js'
    yield 'editor.js'


@TownApp.webasset('fullcalendar')
def get_fullcalendar_asset() -> Iterator[str]:
    yield 'fullcalendar.js'
    yield 'fullcalendar.de.js'
    yield 'fullcalendar.fr.js'
    yield 'reservationcalendar.jsx'
    yield 'reservationcalendar_custom.js'


@TownApp.webasset('occupancycalendar')
def get_occupancycalendar_asset() -> Iterator[str]:
    yield 'occupancycalendar.jsx'
    yield 'occupancycalendar_custom.js'


@TownApp.webasset('staff-chat')
def get_staff_chat_asset() -> Iterator[str]:
    yield 'chat-shared.js'
    yield 'chat-staff.js'


@TownApp.webasset('client-chat')
def get_staff_client_asset() -> Iterator[str]:
    yield 'chat-shared.js'
    yield 'chat-client.js'


@TownApp.webasset('invoicing')
def get_invoicing() -> Iterator[str]:
    yield 'invoicing.js'
