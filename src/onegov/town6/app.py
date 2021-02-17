from onegov.core import utils
from onegov.core.i18n import default_locale_negotiator
from onegov.core.utils import module_path
from onegov.foundation6.integration import FoundationApp
from onegov.town6.initial_content import create_new_organisation
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs, \
    OrgApp
from onegov.town6.theme import TownTheme


class TownApp(OrgApp, FoundationApp):

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', True)
        super().configure_organisation(**cfg)

    @property
    def font_family(self):
        return self.theme_options.get('body-font-family-ui')


@TownApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@TownApp.static_directory()
def get_static_directory():
    return 'static'


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='core', name='theme')
def get_theme():
    return TownTheme()


@TownApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH', 'fr_CH'}


@TownApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [module_path('onegov.town6', 'locale')] \
        + get_org_i18n_localedirs()


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@TownApp.setting(section='i18n', name='locale_negotiator')
def get_locale_negotiator():
    def locale_negotiator(locales, request):
        if request.app.org:
            locales = request.app.org.locales or get_i18n_default_locale()

            if isinstance(locales, str):
                locales = (locales, )

            return default_locale_negotiator(locales, request) or locales[0]
        else:
            return default_locale_negotiator(locales, request)
    return locale_negotiator


@TownApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@TownApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles():
    return ('admin', 'editor')


@TownApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles():
    return ('admin', 'editor')


@TownApp.setting(section='org', name='require_complete_userprofile')
def get_require_complete_userprofile():
    return False


@TownApp.setting(section='org', name='is_complete_userprofile')
def get_is_complete_userprofile_handler():
    def is_complete_userprofile(request, username):
        return True

    return is_complete_userprofile


@TownApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget():
    return None


@TownApp.setting(section='org', name='public_ticket_messages')
def get_public_ticket_messages():
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


@TownApp.webasset_path()
def get_js_path():
    return 'assets/js'


@TownApp.webasset_path()
def get_css_path():
    return 'assets/css'


@TownApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@TownApp.webasset('common')
def get_common_asset():
    yield 'global.js'
    yield 'polyfills.js'
    yield 'jquery.datetimepicker.css'
    yield 'locale.js'
    yield 'modernizr.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'react.js'
    yield 'react-dom.js'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'typeahead.jsx'
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
    yield 'toggle.js'
    yield 'common.js'
    yield '_blank.js'
