from onegov.core import Framework, utils
from onegov.redesign_test.theme.foundation6_theme import RedesignTheme


class RedesignApp(Framework):
    pass


@RedesignApp.template_directory()
def get_template_directory():
    return 'templates'


@RedesignApp.static_directory()
def get_static_directory():
    return 'static'


@RedesignApp.setting(section='core', name='theme')
def get_theme():
    return RedesignTheme()


@RedesignApp.webasset_path()
def get_js_path():
    return 'assets/js'


@RedesignApp.webasset_path()
def get_foundation_js_path():
    return utils.module_path('onegov.foundation6', 'precompiled')


@RedesignApp.webasset_path()
def get_css_path():
    return 'assets/css'


@RedesignApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@RedesignApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.redesign_test', 'locale'),
    ]


@RedesignApp.webasset('foundation-js')
def get_foundation_js_assets():
    yield 'foundation.min.js'
