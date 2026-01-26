from __future__ import annotations

from functools import cached_property
from more.content_security import SELF
from onegov.core import Framework
from onegov.core import utils
from onegov.core.framework import default_content_security_policy
from onegov.file import DepotApp
from onegov.form import FormApp
from onegov.quill import QuillApp
from onegov.swissvotes.models import Principal
from onegov.swissvotes.theme import SwissvotesTheme
from onegov.user import UserApp


from typing import overload
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from more.content_security import ContentSecurityPolicy


class SwissvotesApp(Framework, FormApp, QuillApp, DepotApp, UserApp):
    """ The swissvotes application. Include this in your onegov.yml to serve
    it with onegov-server.

    """

    serve_static_files = True

    @cached_property
    def principal(self) -> Principal:
        return Principal()

    @cached_property
    def static_content_pages(self) -> set[str]:
        return {'home', 'disclaimer', 'imprint', 'data-protection'}

    @overload
    def get_cached_dataset(self, format: Literal['csv']) -> str: ...
    @overload
    def get_cached_dataset(self, format: Literal['xlsx']) -> bytes: ...

    def get_cached_dataset(
        self,
        format: Literal['csv', 'xlsx']
    ) -> str | bytes:
        """ Gets or creates the dataset in the requested format.

        We store the dataset using the last modified timestamp - this way, we
        have a version of past datasets. Note that we don't delete any old
        datasets.

        """
        from onegov.swissvotes.collections import SwissVoteCollection

        assert format in ('csv', 'xlsx')

        votes = SwissVoteCollection(self)
        date = votes.last_modified
        filename = f'dataset-{date.timestamp() if date else ""}.{format}'
        mode = 'b' if format == 'xlsx' else ''

        fs = self.filestorage
        assert fs is not None

        if not fs.exists(filename):
            with fs.open(filename, f'w{mode}') as file:
                getattr(votes, f'export_{format}')(file)

        with fs.open(filename, f'r{mode}') as file:
            result = file.read()
        return result

    def configure_mfg_api_token(
        self,
        *,
        mfg_api_token: str | None = None,
        **cfg: Any
    ) -> None:
        """ Configures the Museum für Gestaltung API Token. """
        self.mfg_api_token = mfg_api_token

    def configure_bs_api_token(
            self,
            *,
            bs_api_token: str | None = None,
            **cfg: Any
    ) -> None:
        """ Configures the Plakatsammlung Basel API Token. """
        self.bs_api_token = bs_api_token


@SwissvotesApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@SwissvotesApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@SwissvotesApp.setting(section='core', name='theme')
def get_theme() -> SwissvotesTheme:
    return SwissvotesTheme()


@SwissvotesApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.swissvotes', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@SwissvotesApp.setting(section='i18n', name='locales')
def get_i18n_used_locales() -> set[str]:
    return {'de_CH', 'fr_CH', 'en_US'}


@SwissvotesApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale() -> str:
    return 'de_CH'


@SwissvotesApp.setting(section='content_security_policy', name='default')
def swissvotes_content_security_policy() -> ContentSecurityPolicy:
    policy = default_content_security_policy()
    policy.connect_src.add(SELF)
    policy.connect_src.add('https://stats.seantis.ch')
    policy.connect_src.add('https://mstdn.social')
    policy.img_src.add('https://www.emuseum.ch')
    policy.script_src.add('https://stats.seantis.ch')
    return policy


@SwissvotesApp.webasset_path()
def get_shared_assets_path() -> str:
    return utils.module_path('onegov.shared', 'assets/js')


@SwissvotesApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@SwissvotesApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@SwissvotesApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@SwissvotesApp.webasset('frameworks')
def get_frameworks_asset() -> Iterator[str]:
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
    yield 'react.js'
    yield 'react-dom.js'
    yield 'react-dropdown-tree-select.js'
    yield 'react-dropdown-tree-select.css'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'jquery.datetimepicker.css'
    yield 'jquery.datetimepicker.js'
    yield 'datetimepicker.js'
    yield 'dropzone.js'


@SwissvotesApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield 'common.js'
    yield 'policy-selector.jsx'
    yield 'image-gallery.js'


@SwissvotesApp.webasset('mastodon')
def get_mastodon_asset() -> Iterator[str]:
    yield 'mastodon-timeline.js'
    yield 'mastodon-timeline.css'


@SwissvotesApp.webasset('stats')
def get_stats_asset() -> Iterator[str]:
    yield 'stats.js'
