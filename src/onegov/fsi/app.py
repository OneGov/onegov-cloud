from onegov.core import utils
from onegov.fsi.initial_content import create_new_organisation
from onegov.fsi.theme import FsiTheme
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs


class FsiApp(OrgApp):

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)


@FsiApp.template_directory()
def get_template_directory():
    return 'templates'


@OrgApp.static_directory()
def get_static_directory():
    return 'static'


@FsiApp.setting(section='core', name='theme')
def get_theme():
    return FsiTheme()


@FsiApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@FsiApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.fsi', 'locale')
    return [mine] + get_org_i18n_localedirs()


@FsiApp.webasset_path()
def get_js_path():
    return 'assets/js'


@FsiApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@FsiApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'ifs.js'
