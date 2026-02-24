from __future__ import annotations

import re
import shlex
import subprocess

from functools import cached_property
from io import BytesIO
from markupsafe import Markup
from onegov.core import utils
from onegov.core.orm.types import JSON
from onegov.core.static import StaticFile
from onegov.org import OrgApp
from onegov.org.app import get_common_asset as default_common_asset
from onegov.org.app import get_i18n_localedirs as get_org_i18n_localedirs
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.winterthur.initial_content import create_new_organisation
from onegov.winterthur.roadwork import RoadworkClient
from onegov.winterthur.roadwork import RoadworkConfig
from onegov.winterthur.theme import WinterthurTheme
from pathlib import Path
from sqlalchemy import cast
from tempfile import TemporaryDirectory


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.cache import RedisCacheRegion
    from onegov.org.models import Organisation
    from onegov.winterthur.request import WinterthurRequest
    from webob import Response


class WinterthurApp(OrgApp):

    serve_static_files = True

    frame_ancestors = {
        'https://winterthur.ch',
        'https://*.winterthur.ch',
        'http://localhost:8000',
    }

    # disable same site cookie protection as we need to run inside iframes
    # with cookies enabled
    same_site_cookie_policy = None

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = False,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:

        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )

    def enable_iframes(self, request: WinterthurRequest) -> None:
        request.content_security_policy.frame_ancestors |= self.frame_ancestors
        request.include('iframe-resizer')

    @property
    def roadwork_cache(self) -> RedisCacheRegion:
        # the expiration time is high here, as the expiration is more closely
        # managed by the roadwork client
        return self.get_cache('roadwork', expiration_time=60 * 60 * 24)

    @cached_property
    def roadwork_client(self) -> RoadworkClient:
        config = RoadworkConfig.lookup()

        # FIXME: We should probably raise an error if the configuration
        #        is incomplete...
        return RoadworkClient(
            cache=self.roadwork_cache,
            hostname=config.hostname,  # type:ignore[arg-type]
            endpoint=config.endpoint,
            username=config.username,  # type:ignore[arg-type]
            password=config.password  # type:ignore[arg-type]
        )

    @property
    def mission_report_legend(self) -> Markup:
        from onegov.winterthur.views.settings import DEFAULT_LEGEND
        settings = self.org.meta.get('mission_report_settings') or {}

        if 'legend' in settings:
            # NOTE: We need to wrap this in Markup. It would be cleaner
            #       if we had a proxy settings object with dict_property
            return Markup(settings['legend'])  # nosec: B704

        return DEFAULT_LEGEND

    @property
    def hide_civil_defence_field(self) -> bool:
        settings = self.org.meta.get('mission_report_settings') or {}
        hide = settings.get('hide_civil_defence_field', False)

        return hide

    def static_file(self, path: str) -> StaticFile:
        return StaticFile(path, version=self.version)

    def get_shift_schedule_image(self) -> BytesIO | None:
        """ Gets or creates an image of the latest public pdf.

        We store the image using the last modified timestamp - this way, we
        have a version of past images. Note that we don't delete any old
        images of shift schedules.

        """

        query = GeneralFileCollection(self.session()).query().filter(
            GeneralFile.published.is_(True),
            cast(GeneralFile.reference, JSON)['content_type']
            == 'application/pdf'
        )
        query = query.order_by(GeneralFile.created.desc())
        file = query.first()

        if not file:
            return None

        upload_time = file.created.timestamp()
        filename = f'shift-schedule-{upload_time}.png'

        fs = self.filestorage
        assert fs is not None
        if not fs.exists(filename):
            with TemporaryDirectory() as directory:
                path = Path(directory)

                with (path / 'input.pdf').open('wb') as pdf:
                    pdf.write(file.reference.file.read())

                process = subprocess.run((  # nosec:B603
                    'gs',

                    # disable read/writes outside of the given files
                    '-dSAFER',
                    '-dPARANOIDSAFER',

                    # do not block for any reason
                    '-dBATCH',
                    '-dNOPAUSE',
                    '-dNOPROMPT',

                    # limit output messages
                    '-dQUIET',
                    '-sstdout=/dev/null',

                    # format the page for thumbnails
                    '-dPDFFitPage',

                    # render in high resolution before downscaling to 300 dpi
                    '-r300',
                    '-dDownScaleFactor=1',

                    # only use the first page
                    '-dLastPage=1',

                    # output to png
                    '-sDEVICE=png16m',
                    '-sOutputFile={}'.format(
                        shlex.quote(str(path / 'preview.png'))
                    ),

                    # force landscape orientation in postscript
                    '-c',
                    '<</Orientation 3>> setpagedevice',
                    '-f',

                    # from pdf
                    str(path / 'input.pdf')
                ))

                process.check_returncode()

                with (
                    (path / 'preview.png').open('rb') as input,
                    fs.open(filename, 'wb') as output
                ):
                    # NOTE: Bug in type hints of FS
                    output.write(input.read())  # type:ignore

        with fs.open(filename, 'rb') as input:
            # NOTE: Bug in type hints of FS
            return BytesIO(input.read())  # type:ignore


@WinterthurApp.tween_factory()
def enable_iframes_tween_factory(
    app: WinterthurApp,
    handler: Callable[[WinterthurRequest], Response]
) -> Callable[[WinterthurRequest], Response]:
    iframe_paths = (
        r'/streets.*',
        r'/director(y|ies|y-submission/.*)',
        r'/ticket/.*',
        r'/mission-report.*',
        r'/roadwork.*',
        r'/daycare-subsidy-calculator',
        r'/events.*',
        r'/event.*',
    )

    iframe_path_re = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_tween(request: WinterthurRequest) -> Response:
        """ Enables iframes on matching paths. """

        result = handler(request)

        if iframe_path_re.match(request.path_info or ''):
            request.app.enable_iframes(request)

        return result

    return enable_iframes_tween


@WinterthurApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@OrgApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@WinterthurApp.setting(section='core', name='theme')
def get_theme() -> WinterthurTheme:
    return WinterthurTheme()


@WinterthurApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[WinterthurApp, str], Organisation]:
    return create_new_organisation


@WinterthurApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget() -> str:
    return 'inline'


@WinterthurApp.setting(section='org', name='default_event_search_widget')
def get_default_event_search_widget() -> str:
    return 'inline'


@WinterthurApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    mine = utils.module_path('onegov.winterthur', 'locale')
    return [mine, *get_org_i18n_localedirs()]


@WinterthurApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@WinterthurApp.webasset_output()
def get_webasset_output() -> str:
    return 'assets/bundles'


@WinterthurApp.webasset('inline-search')
def get_inline_search_asset() -> Iterator[str]:
    yield 'inline-search.js'


@WinterthurApp.webasset('street-search')
def get_street_search_asset() -> Iterator[str]:
    yield 'wade.js'
    yield 'string-score.js'
    yield 'street-search.js'


@WinterthurApp.webasset('iframe-resizer')
def get_iframe_resizer() -> Iterator[str]:
    yield 'iframe-resizer-options.js'
    yield 'iframe-resizer-contentwindow.js'


@WinterthurApp.webasset('iframe-enhancements')
def get_iframe_enhancements() -> Iterator[str]:
    yield 'iframe-enhancements.js'


@WinterthurApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'winterthur.js'
