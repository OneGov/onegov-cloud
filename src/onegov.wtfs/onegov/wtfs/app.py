from cached_property import cached_property
from onegov.core import Framework
from onegov.core import utils
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.models import Principal
from onegov.wtfs.models import PaymentType
from onegov.wtfs.theme import WtfsTheme


class WtfsApp(Framework, FormApp, DepotApp):
    """ The Wtfs application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    @cached_property
    def principal(self):
        return Principal()

    def add_initial_content(self):
        session = self.session()
        municipalities = MunicipalityCollection(session)
        for name, bfs_number in (
            ('Adlikon', 21),
            ('Aesch', 241),
            ('Aeugst am Albis', 1),
            ('Altikon', 211),
            ('Andelfingen', 30),
            ('Bachenbülach', 51),
            ('Bachs', 81),
            ('Bäretswil', 111),
            ('Bauma', 171),
            ('Benken', 22),
            ('Berg am Irchel', 23),
            ('Bertschikon', 212),
            ('Birmensdorf', 242),
            ('Bonstetten', 3),
            ('Boppelsen', 82),
            ('Brütten', 213),
            ('Buch am Irchel', 24),
            ('Dachsen', 25),
            ('Dägerlen', 214)
        ):
            municipalities.add(
                name=name,
                bfs_number=bfs_number
            )
        session.add(PaymentType(name='normal', _price_per_quantity=700))
        session.add(PaymentType(name='spezial', _price_per_quantity=850))


@WtfsApp.static_directory()
def get_static_directory():
    return 'static'


@WtfsApp.template_directory()
def get_template_directory():
    return 'templates'


@WtfsApp.setting(section='core', name='theme')
def get_theme():
    return WtfsTheme()


@WtfsApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.wtfs', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@WtfsApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH'}


@WtfsApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@WtfsApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@WtfsApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WtfsApp.webasset_path()
def get_css_path():
    return 'assets/css'


@WtfsApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@WtfsApp.webasset('frameworks')
def get_frameworks_asset():
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'tablesaw.css'
    yield 'tablesaw.jquery.js'
    yield 'tablesaw-create.js'
    yield 'tablesaw-init.js'
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


@WtfsApp.webasset('common')
def get_common_asset():
    yield 'common.js'
