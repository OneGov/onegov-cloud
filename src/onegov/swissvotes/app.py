from functools import cached_property
from more.content_security import SELF
from more.content_security import UNSAFE_EVAL
from more.content_security import UNSAFE_INLINE
from onegov.core import Framework
from onegov.core import utils
from onegov.core.framework import default_content_security_policy
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.quill import QuillApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.theme import SwissvotesTheme
from onegov.user import UserApp


class SwissvotesApp(Framework, FormApp, QuillApp, DepotApp, UserApp):
    """ The swissvotes application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    @cached_property
    def principal(self):
        return Principal()

    @cached_property
    def static_content_pages(self):
        return {'home', 'disclaimer', 'imprint', 'data-protection'}

    def get_cached_dataset(self, format):
        """ Gets or creates the dataset in the requested format.

        We store the dataset using the last modified timestamp - this way, we
        have a version of past datasets. Note that we don't delete any old
        datasets.

        """
        from onegov.swissvotes.collections import SwissVoteCollection

        assert format in ('csv', 'xlsx')

        votes = SwissVoteCollection(self)
        last_modified = votes.last_modified
        last_modified = last_modified.timestamp() if last_modified else ''
        filename = f'dataset-{last_modified}.{format}'
        mode = 'b' if format == 'xlsx' else ''

        if not self.filestorage.exists(filename):
            with self.filestorage.open(filename, f'w{mode}') as file:
                getattr(votes, f'export_{format}')(file)

        with self.filestorage.open(filename, f'r{mode}') as file:
            result = file.read()
        return result

    def configure_mfg_api_token(self, **cfg):
        """ Configures the Museum für Gestaltung API Token. """
        self.mfg_api_token = cfg.get('mfg_api_token', None)


@SwissvotesApp.static_directory()
def get_static_directory():
    return 'static'


@SwissvotesApp.template_directory()
def get_template_directory():
    return 'templates'


@SwissvotesApp.setting(section='core', name='theme')
def get_theme():
    return SwissvotesTheme()


@SwissvotesApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.swissvotes', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@SwissvotesApp.setting(section='i18n', name='locales')
def get_i18n_used_locales():
    return {'de_CH', 'fr_CH', 'en_US'}


@SwissvotesApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@SwissvotesApp.setting(section='content_security_policy', name='default')
def org_content_security_policy():
    policy = default_content_security_policy()
    policy.connect_src.add(SELF)
    policy.connect_src.add('https://stats.seantis.ch')
    policy.connect_src.add('https://mstdn.social')
    policy.img_src.add('https://www.emuseum.ch')
    policy.script_src.add('https://stats.seantis.ch')
    policy.script_src.remove(UNSAFE_EVAL)
    policy.script_src.remove(UNSAFE_INLINE)
    return policy


@SwissvotesApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@SwissvotesApp.webasset_path()
def get_js_path():
    return 'assets/js'


@SwissvotesApp.webasset_path()
def get_css_path():
    return 'assets/css'


@SwissvotesApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@SwissvotesApp.webasset('frameworks')
def get_frameworks_asset():
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'jquery.tablesorter.js'
    yield 'tablesaw.css'
    yield 'tablesaw.jquery.js'
    yield 'tablesaw-create.js'
    yield 'tablesaw-translations.js'
    yield 'tablesaw-init.js'
    yield 'd3.js'
    yield 'd3.chart.bar.js'
    yield 'foundation.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'sortable.js'
    yield 'sortable_custom.js'
    yield 'react.min.js'
    yield 'react-dom.min.js'
    yield 'react-dropdown-tree-select.js'
    yield 'react-dropdown-tree-select.css'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'dropzone.js'


@SwissvotesApp.webasset('common')
def get_common_asset():
    yield 'common.js'
    yield 'policy-selector.jsx'
    yield 'image-gallery.js'


@SwissvotesApp.webasset('mastodon')
def get_mastodon_asset():
    yield 'mastodon-timeline.js'
    yield 'mastodon-timeline.css'


@SwissvotesApp.webasset('stats')
def get_stats_asset():
    yield 'stats.js'
