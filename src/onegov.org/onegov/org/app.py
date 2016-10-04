""" Contains the base application used by other applications. """

from chameleon import PageTemplate
from collections import defaultdict
from contextlib import contextmanager
from dectate import directive
from onegov.core import Framework, utils
from onegov.file import DepotApp
from onegov.gis import MapboxApp
from onegov.libres import LibresIntegration
from onegov.org import directives
from onegov.org.homepage_widgets import transform_homepage_structure
from onegov.org.initial_content import create_new_organisation
from onegov.org.models import Topic, Organisation
from onegov.org.request import OrgRequest
from onegov.org.theme import OrgTheme
from onegov.page import PageCollection
from onegov.search import ElasticsearchApp
from onegov.ticket import TicketCollection
from sqlalchemy.orm.attributes import flag_modified


class OrgApp(Framework, LibresIntegration, ElasticsearchApp, MapboxApp,
             DepotApp):

    serve_static_files = True
    request_class = OrgRequest

    #: org directives
    homepage_widget = directive(directives.HomepageWidgetAction)

    def is_allowed_application_id(self, application_id):
        """ Stops onegov.server from ever passing the request to the org
        application, if the schema does not exist. This way we can host
        onegov.org in a way that allows all requests to *.example.org

        If the schema for ``newyork.example.org`` exists, the request is
        handled. If the schema does not exist, the request is not handled.

        Here we basically decide if an org exists or not.

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

    def configure_application(self, **cfg):
        super().configure_application(**cfg)

        if self.has_database_connection:
            schema_prefix = self.namespace + '-'

            self.known_schemas = set(
                s for s in self.session_manager.list_schemas()
                if s.startswith(schema_prefix)
            )

    @property
    def org(self):
        """ Returns the cached version of the organisation. Since the it rarely
        ever changes, it makes sense to not hit the database for it every
        time.

        As a consequence, changes to the organisation object are not
        propagated, unless you use :meth:`update_org` or use the ORM directly.

        """
        org = self.cache.get_or_create(
            'org',
            creator=self.load_org,
            should_cache_fn=lambda org: org is not None
        )

        if org is not None:
            return self.session().merge(org, load=False)

    def load_org(self):
        """ Loads the org from the SQL database. """
        return self.session().query(Organisation).first()

    @contextmanager
    def update_org(self):
        """ Yields the current org for an update. Use this instead of
        updating the org directly, because caching is involved. It's rather
        easy to otherwise update it wrongly.

        Example::
            with app.update_org() as org:
                org.name = 'New Name'

        """

        session = self.session()

        org = session.merge(self.org)
        yield org

        # nested entries in the meta json field are not detected as modified
        flag_modified(org, 'meta')

        session.flush()

        self.update_homepage_template()
        self.cache.delete('org')

    @property
    def homepage_template(self):
        """ Returns the homepage template built from the homepage content
        setting which contains a simplified and limited xml to define the
        homepage.

        """
        return self.cache.get_or_create(
            'homepage_template', self.load_homepage_template)

    def load_homepage_template(self):
        homepage_structure = self.org.meta.get('homepage_structure')

        if homepage_structure:
            return PageTemplate(
                transform_homepage_structure(self, homepage_structure))
        else:
            return PageTemplate('')

    def update_homepage_template(self):
        self.cache.delete('homepage_template')

    @property
    def ticket_count(self):
        return self.cache.get_or_create('ticket_count', self.load_ticket_count)

    def load_ticket_count(self):
        return TicketCollection(self.session()).get_count()

    def update_ticket_count(self):
        return self.cache.delete('ticket_count')

    def send_email(self, **kwargs):
        """ Wraps :meth:`onegov.core.framework.Framework.send_email`, setting
        the reply_to address by using the reply address from the organisation
        settings.

        """

        assert 'reply_to' in self.org.meta

        reply_to = "{} <{}>".format(self.org.name, self.org.meta['reply_to'])

        return super().send_email(reply_to=reply_to, **kwargs)

    @property
    def theme_options(self):
        return self.org.theme_options or {}

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


@OrgApp.webasset_path()
def get_shared_assets_path():
    return utils.module_path('onegov.shared', 'assets/js')


@OrgApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs():
    return [
        utils.module_path('onegov.org', 'locale'),
        utils.module_path('onegov.form', 'locale'),
        utils.module_path('onegov.user', 'locale')
    ]


@OrgApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de_CH'


@OrgApp.static_directory()
def get_static_directory():
    return 'static'


@OrgApp.template_directory()
def get_template_directory():
    return 'templates'


@OrgApp.setting(section='core', name='theme')
def get_theme():
    return OrgTheme()


@OrgApp.setting(section='org', name='enable_user_registration')
def get_enable_user_registration():
    return True


@OrgApp.setting(section='org', name='enable_yubikey')
def get_enable_yubikey():
    return False


@OrgApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory():
    return create_new_organisation


@OrgApp.webasset_path()
def get_js_path():
    return 'assets/js'


@OrgApp.webasset_path()
def get_css_path():
    return 'assets/css'


@OrgApp.webasset_output()
def get_webasset_output():
    return 'assets/bundles'


@OrgApp.webasset('sortable')
def get_sortable_asset():
    yield 'sortable.js'
    yield 'sortable_custom.js'


@OrgApp.webasset('fullcalendar')
def get_fullcalendar_asset():
    yield 'fullcalendar.css'
    yield 'fullcalendar.js'
    yield 'fullcalendar.de.js'
    yield 'reservationcalendar.jsx'
    yield 'reservationcalendar_custom.js'


@OrgApp.webasset('check_contrast')
def get_check_contrast_asset():
    yield 'check_contrast.js'


@OrgApp.webasset('check_password')
def get_check_password_asset():
    yield 'zxcvbn.js'
    yield 'check_password.js'


@OrgApp.webasset('code_editor')
def get_code_editor_asset():
    yield 'ace.js'
    yield 'ace-mode-form.js'
    yield 'ace-mode-xml.js'
    yield 'ace-theme-tomorrow.js'
    yield 'code_editor.js'


@OrgApp.webasset('editor')
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
@OrgApp.webasset('redactor', filters={'js': None})
def get_redactor_asset():
    yield 'redactor.min.js'
    yield 'redactor.css'


@OrgApp.webasset('dropzone')
def get_dropzone_asset():
    yield 'dropzone.js'


@OrgApp.webasset('editalttext')
def get_editalttext_asset():
    yield 'editalttext.js'


@OrgApp.webasset('common')
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
    yield 'moment.js'
    yield 'moment.de.js'
    yield 'jquery.datetimepicker.js'
    yield 'jquery.mousewheel.js'
    yield 'jquery.popupoverlay.js'
    yield 'jquery.load.js'
    yield 'videoframe.js'
    yield 'datetimepicker.js'
    yield 'url.js'
    yield 'date-range-selector.js'
    yield 'lazyalttext.js'
    yield 'lazysizes.js'
    yield 'common.js'
