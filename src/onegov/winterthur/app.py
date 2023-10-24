import re
import subprocess

from functools import cached_property
from io import BytesIO
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

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)

    def enable_iframes(self, request):
        request.content_security_policy.frame_ancestors |= self.frame_ancestors
        request.include('iframe-resizer')

    @property
    def roadwork_cache(self):
        # the expiration time is high here, as the expiration is more closely
        # managed by the roadwork client
        return self.get_cache('roadwork', expiration_time=60 * 60 * 24)

    @cached_property
    def roadwork_client(self):
        config = RoadworkConfig.lookup()

        return RoadworkClient(
            cache=self.roadwork_cache,
            hostname=config.hostname,
            endpoint=config.endpoint,
            username=config.username,
            password=config.password
        )

    @property
    def mission_report_legend(self):
        from onegov.winterthur.views.settings import DEFAULT_LEGEND
        settings = self.org.meta.get('mission_report_settings') or {}

        if 'legend' in settings:
            return settings['legend']

        return DEFAULT_LEGEND

    @property
    def hide_civil_defence_field(self):
        settings = self.org.meta.get('mission_report_settings') or {}
        hide = settings.get('hide_civil_defence_field', False)

        return hide

    def static_file(self, path):
        return StaticFile(path, version=self.version)

    def get_shift_schedule_image(self):
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
            return

        upload_time = file.created.timestamp()
        filename = f'shift-schedule-{upload_time}.png'

        if not self.filestorage.exists(filename):
            with TemporaryDirectory() as directory:
                path = Path(directory)

                with (path / 'input.pdf').open('wb') as pdf:
                    pdf.write(file.reference.file.read())

                process = subprocess.run((
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
                    f'-r{300}',
                    f'-dDownScaleFactor={1}',

                    # only use the first page
                    '-dLastPage=1',

                    # output to png
                    '-sDEVICE=png16m',
                    f'-sOutputFile={path / "preview.png"}',

                    # from pdf
                    str(path / 'input.pdf')
                ))

                process.check_returncode()

                with (path / 'preview.png').open('rb') as input:
                    with self.filestorage.open(filename, 'wb') as output:
                        output.write(input.read())

        with self.filestorage.open(filename, 'rb') as input:
            return BytesIO(input.read())


@WinterthurApp.tween_factory()
def enable_iframes_tween_factory(app, handler):
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

    iframe_paths = re.compile(rf"({'|'.join(iframe_paths)})")

    def enable_iframes_tween(request):
        """ Enables iframes on matching paths. """

        result = handler(request)

        if iframe_paths.match(request.path_info):
            request.app.enable_iframes(request)

        return result

    return enable_iframes_tween


@WinterthurApp.template_directory()
def get_template_directory():
    return 'templates'


@OrgApp.static_directory()
def get_static_directory():
    return 'static'


@WinterthurApp.setting(section='core', name='theme')
def get_theme():
    return WinterthurTheme()


@WinterthurApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@WinterthurApp.setting(section='org', name='default_directory_search_widget')
def get_default_directory_search_widget():
    return 'inline'


@WinterthurApp.setting(section='org', name='default_event_search_widget')
def get_default_event_search_widget():
    return 'inline'


@WinterthurApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    mine = utils.module_path('onegov.winterthur', 'locale')
    return [mine] + get_org_i18n_localedirs()


@WinterthurApp.webasset_path()
def get_js_path():
    return 'assets/js'


@WinterthurApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@WinterthurApp.webasset('street-search')
def get_search_asset():
    yield 'wade.js'
    yield 'string-score.js'
    yield 'street-search.js'


@WinterthurApp.webasset('iframe-resizer')
def get_iframe_resizer():
    yield 'iframe-resizer-options.js'
    yield 'iframe-resizer-contentwindow.js'


@WinterthurApp.webasset('iframe-enhancements')
def get_iframe_enhancements():
    yield 'iframe-enhancements.js'


@WinterthurApp.webasset('common')
def get_common_asset():
    yield from default_common_asset()
    yield 'winterthur.js'
