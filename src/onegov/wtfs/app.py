from functools import cached_property
from onegov.core import Framework
from onegov.core import utils
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.user import UserApp
from onegov.wtfs.models import Principal
from onegov.wtfs.models import PaymentType
from onegov.wtfs.theme import WtfsTheme


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


class WtfsApp(Framework, FormApp, DepotApp, UserApp):
    """ The Wtfs application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    @cached_property
    def principal(self) -> Principal:
        return Principal()

    def add_initial_content(self) -> None:
        session = self.session()
        session.add(PaymentType(name='normal', _price_per_quantity=700))
        session.add(PaymentType(name='spezial', _price_per_quantity=850))


@WtfsApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@WtfsApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@WtfsApp.setting(section='core', name='theme')
def get_theme() -> WtfsTheme:
    return WtfsTheme()


@WtfsApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.wtfs', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@WtfsApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH'}


@WtfsApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@WtfsApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@WtfsApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@WtfsApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@WtfsApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@WtfsApp.webasset('frameworks')
def get_frameworks_asset() -> 'Iterator[str]':
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'foundation.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'react.js'
    yield 'react-dom.js'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'form-adjust.js'


@WtfsApp.webasset('common')
def get_common_asset() -> 'Iterator[str]':
    yield 'common.js'
