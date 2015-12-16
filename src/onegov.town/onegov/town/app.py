""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

import transaction

from cached_property import cached_property
from collections import defaultdict
from contextlib import contextmanager
from onegov.core import Framework
from onegov.core import utils
from onegov.libres import LibresIntegration
from onegov.page import PageCollection
from onegov.search import ElasticsearchApp
from onegov.shared import asset
from onegov.ticket import TicketCollection
from onegov.town import log
from onegov.town.initial_content import add_builtin_forms
from onegov.town.models import Town, Topic
from onegov.town.theme import TownTheme
from webassets import Bundle


class TownApp(Framework, LibresIntegration, ElasticsearchApp):
    """ The town application. Include this in your onegov.yml to serve it
    with onegov-server.

    """

    serve_static_files = True

    @property
    def town(self):
        """ Returns the cached version of the town. Since the town rarely
        ever changes, it makes sense to not hit the database for it every
        time.

        As a consequence, changes to the town object are not propagated,
        unless you use :meth:`update_town` or use the ORM directly.

        """
        return self.session().merge(
            self.cache.get_or_create('town', self.load_town), load=False)

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
            town_schemas = [
                s for s in self.session_manager.list_schemas()
                if s.startswith(schema_prefix)
            ]

            for schema in town_schemas:
                self.session_manager.set_current_schema(schema)

                session = self.session()
                add_builtin_forms(session)
                session.flush()
                transaction.commit()

            log.info('Updated all builtin forms')

    @property
    def theme_options(self):
        return self.town.theme_options or {}

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.town', 'assets')

    @cached_property
    def webassets_bundles(self):

        jsminifier = 'rjsmin'

        confirm = Bundle(
            'js/confirm.jsx',
            filters='jsx',
            output='bundles/confirm.bundle.js'
        )

        dropzone = Bundle(
            'js/dropzone.js',
            filters=jsminifier,
            output='bundles/dropzone.bundle.js'
        )

        typeahead = Bundle(
            'js/typeahead.jsx',
            filters='jsx',
            output='bundles/typeahead.bundle.js'
        )

        # do NOT minify the redactor, or the copyright notice goes away, which
        # is something we are not allowed to do per our license
        # ->
        redactor = Bundle(
            'js/redactor.min.js',
            output='bundles/redactor.bundle.js'
        )
        redactor_theme = Bundle(
            'css/redactor.css',
            output='bundles/redactor.bundle.css'
        )
        # <-

        editor = Bundle(
            'js/bufferbuttons.js',
            'js/definedlinks.js',
            'js/filemanager.js',
            'js/imagemanager.js',
            'js/redactor.de.js',
            'js/input_with_button.js',
            'js/editor.js',
            filters=jsminifier,
            output='bundles/editor.bundle.js'
        )

        code_editor = Bundle(
            'js/ace.js',
            'js/ace-mode-form.js',
            'js/ace-theme-tomorrow.js',
            'js/code_editor.js',
            filters=jsminifier,
            output='bundles/code_editor.bundle.js'
        )

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/intercooler.js',
            'js/underscore.js',
            'js/react.js',
            asset('js/form_dependencies.js'),
            confirm,
            typeahead,
            'js/jquery.datetimepicker.js',
            'js/datetimepicker.js',
            'js/jquery.popupoverlay.js',
            'js/common.js',
            filters=jsminifier,
            output='bundles/common.bundle.js'
        )

        common_css = Bundle(
            'css/jquery.datetimepicker.css',
            filters='cssmin',
            output='bundles/common.bundle.css',
        )

        fullcalendar = Bundle(
            'js/moment.js',
            'js/moment.de.js',
            'js/fullcalendar.js',
            'js/fullcalendar.de.js',
            'js/fullcalendar_custom.js',
            filters=jsminifier,
            output='bundles/fullcalendar.bundle.js'
        )

        fullcalendar_css = Bundle(
            'css/fullcalendar.css',
            filters='cssmin',
            output='bundles/fullcalendar.bundle.css'
        )

        check_password = Bundle(
            'js/zxcvbn.js',
            'js/check_password.js',
            filters=jsminifier,
            output='bundles/check_password.bundle.js'
        )

        check_contrast = Bundle(
            'js/check_contrast.js',
            filters=jsminifier,
            output='bundles/check_contrast.bundle.js'
        )

        events = Bundle(
            'js/url.js',
            'js/events.js',
            filters=jsminifier,
            output='bundles/events.bundle.js'
        )

        sortable = Bundle(
            'js/sortable.js',
            'js/sortable_custom.js',
            filters=jsminifier,
            output='bundles/sortable.bundle.js'
        )

        return {
            'common': common,
            'common_css': common_css,
            'dropzone': dropzone,
            'redactor': redactor,
            'redactor_theme': redactor_theme,
            'editor': editor,
            'code_editor': code_editor,
            'check_password': check_password,
            'check_contrast': check_contrast,
            'fullcalendar': fullcalendar,
            'fullcalendar_css': fullcalendar_css,
            'events': events,
            'sortable': sortable
        }


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
