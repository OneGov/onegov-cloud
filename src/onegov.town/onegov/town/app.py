""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from collections import defaultdict
from contextlib import contextmanager
from onegov.core import Framework
from onegov.core import utils
from onegov.gis import MapboxApp
from onegov.libres import LibresIntegration
from onegov.page import PageCollection
from onegov.search import ElasticsearchApp
from onegov.ticket import TicketCollection
from onegov.town.models import Town, Topic
from onegov.town.theme import TownTheme
from sqlalchemy.orm.attributes import flag_modified


class TownApp(Framework, LibresIntegration, ElasticsearchApp, MapboxApp):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """

    serve_static_files = True

    def is_allowed_application_id(self, application_id):
        """ Stops onegov.server from ever passing the request to the town
        application, if the schema does not exist. This way we can host
        onegov.town in a way that allows all requests to *.onegovcloud.ch.

        If the schema for ``newyork.onegovcloud.ch`` exists, the request is
        handled. If the schema does not exist, the request is not handled.

        Here we basically decide if a town exists or not.

        """
        schema = self.namespace + '-' + application_id

        if schema in self.known_schemas:
            return True

        # block invalid schemas from ever being checked
        if not self.session_manager.is_valid_schema(schema):
            return False

        # if the schema exists, remember it
        if self.session_manager.is_schema_found_on_database(schema):
            self.known_schemas.add(schema)

            return True

        return False

    @property
    def town(self):
        """ Returns the cached version of the town. Since the town rarely
        ever changes, it makes sense to not hit the database for it every
        time.

        As a consequence, changes to the town object are not propagated,
        unless you use :meth:`update_town` or use the ORM directly.

        """
        town = self.cache.get_or_create(
            'town',
            creator=self.load_town,
            should_cache_fn=lambda town: town is not None
        )

        if town is not None:
            return self.session().merge(town, load=False)

    def load_town(self):
        """ Loads the town from the SQL database. """
        return self.session().query(Town).first()

    @contextmanager
    def update_town(self):
        """ Yields the current town for an update. Use this instead of
        updating the town directly, because caching is involved. It's rather
        easy to otherwise update it wrongly.

        Example::
            with app.update_town() as town:
                town.name = 'New Name'

        """

        session = self.session()

        town = session.merge(self.town)
        yield town

        # nested entries in the meta json field are not detected as modified
        flag_modified(town, 'meta')

        session.flush()

        self.cache.delete('town')

    @property
    def ticket_count(self):
        return self.cache.get_or_create('ticket_count', self.load_ticket_count)

    def load_ticket_count(self):
        return TicketCollection(self.session()).get_count()

    def update_ticket_count(self):
        return self.cache.delete('ticket_count')

    @property
    def homepage_pages(self):
        return self.cache.get_or_create(
            'homepage_pages', self.load_homepage_pages)

    def load_homepage_pages(self):
        pages = PageCollection(self.session()).query()
        pages = pages.filter(Topic.type == 'topic')

        # XXX use JSON/JSONB for this (the attribute is not there if it's
        # false, so this is not too bad speed-wise but it's still awful)
        pages = pages.filter(Topic.meta.contains(
            'is_visible_on_homepage'
        ))

        result = defaultdict(list)
        for page in pages.all():
            if page.is_visible_on_homepage:
                result[page.root.id].append(page)

        for key in result:
            result[key] = list(sorted(
                result[key],
                key=lambda p: utils.normalize_for_url(p.title)
            ))

        return result

    def update_homepage_pages(self):
        return self.cache.delete('homepage_pages')

    def send_email(self, **kwargs):
        """ Wraps :meth:`onegov.core.framework.Framework.send_email`, setting
        the reply_to address by using the reply address from the town
        settings.

        """

        assert 'reply_to' in self.town.meta

        reply_to = "{} <{}>".format(self.town.name, self.town.meta['reply_to'])

        return super().send_email(reply_to=reply_to, **kwargs)

    def configure_application(self, **cfg):
        super().configure_application(**cfg)

        if self.has_database_connection:
            schema_prefix = self.namespace + '-'

            self.known_schemas = set(
                s for s in self.session_manager.list_schemas()
                if s.startswith(schema_prefix)
            )

    @property
    def theme_options(self):
        return self.town.theme_options or {}


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='core', name='theme')
def get_theme():
    return TownTheme()


@TownApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.town', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@TownApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@TownApp.webasset_path()
def get_js_path():
    return 'assets/js'


@TownApp.webasset_path()
def get_css_path():
    return 'assets/css'


@TownApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@TownApp.webasset('sortable')
def get_sortable_asset():
    yield 'sortable.js'
    yield 'sortable_custom.js'


@TownApp.webasset('fullcalendar')
def get_fullcalendar_asset():
    yield 'fullcalendar.css'
    yield 'moment.js'
    yield 'moment.de.js'
    yield 'fullcalendar.js'
    yield 'fullcalendar.de.js'
    yield 'reservationcalendar.jsx'
    yield 'reservationcalendar_custom.js'


@TownApp.webasset('check_contrast')
def get_check_contrast_asset():
    yield 'check_contrast.js'


@TownApp.webasset('check_password')
def get_check_password_asset():
    yield 'zxcvbn.js'
    yield 'check_password.js'


@TownApp.webasset('code_editor')
def get_code_editor_asset():
    yield 'ace.js'
    yield 'ace-mode-form.js'
    yield 'ace-theme-tomorrow.js'
    yield 'code_editor.js'


@TownApp.webasset('editor')
def get_editor_asset():
    yield 'bufferbuttons.js'
    yield 'definedlinks.js'
    yield 'filemanager.js'
    yield 'imagemanager.js'
    yield 'redactor.de.js'
    yield 'input_with_button.js'
    yield 'editor.js'


# do NOT minify the redactor, or the copyright notice goes away, which
# is something we are not allowed to do per our license
@TownApp.webasset('redactor', filters={'js': None})
def get_redactor_asset():
    yield 'redactor.min.js'
    yield 'redactor.css'


@TownApp.webasset('dropzone')
def get_dropzone_asset():
    yield 'dropzone.js'


@TownApp.webasset('common')
def get_common_asset():
    yield 'jquery.datetimepicker.css'
    yield 'locale.js'
    yield 'modernizr.js'
    yield 'jquery.js'
    yield 'fastclick.js'
    yield 'foundation.js'
    yield 'intercooler.js'
    yield 'underscore.js'
    yield 'react.js'
    yield 'form_dependencies.js'
    yield 'confirm.jsx'
    yield 'typeahead.jsx'
    yield 'leaflet'
    yield 'jquery.datetimepicker.js'
    yield 'jquery.mousewheel.js'
    yield 'jquery.popupoverlay.js'
    yield 'videoframe.js'
    yield 'datetimepicker.js'
    yield 'url.js'
    yield 'date-range-selector.js'
    yield 'common.js'
