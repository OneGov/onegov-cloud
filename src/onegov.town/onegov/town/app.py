""" Contains the application which builds on onegov.core and uses
more.chameleon.

It's possible that the chameleon integration is moved to onegov.core in the
future, but for now it is assumed that different applications may want to
use different templating languages.

"""

from cached_property import cached_property
from contextlib import contextmanager
from onegov.core import Framework
from onegov.core import utils
from onegov.town import _
from onegov.town.models import Town
from onegov.town.theme import TownTheme
from webassets import Bundle


class TownApp(Framework):
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
        return self.cache.get_or_create('town', self.load_town)

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
    def theme_options(self):
        return self.town.theme_options or {}

    @cached_property
    def webassets_path(self):
        return utils.module_path('onegov.town', 'assets')

    @cached_property
    def webassets_bundles(self):

        confirm = Bundle(
            'js/confirm.jsx',
            filters='jsx',
            output='bundles/confirm.bundle.js'
        )

        dropzone = Bundle(
            'js/dropzone.js',
            filters='jsmin',
            output='bundles/dropzone.bundle.js'
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
            'js/imagemanager.js',
            'js/redactor.de.js',
            'js/editor.js',
            filters='jsmin',
            output='bundles/editor.bundle.js'
        )

        common = Bundle(
            'js/modernizr.js',
            'js/jquery.js',
            'js/fastclick.js',
            'js/foundation.js',
            'js/intercooler.js',
            'js/underscore.js',
            'js/react.js',
            'js/stickyfooter.js',
            confirm,
            'js/common.js',
            filters='jsmin',
            output='bundles/common.bundle.js'
        )

        return {
            'common': common,
            'dropzone': dropzone,
            'redactor': redactor,
            'redactor_theme': redactor_theme,
            'editor': editor
        }


@TownApp.template_directory()
def get_template_directory():
    return 'templates'


@TownApp.setting(section='core', name='theme')
def get_theme():
    return TownTheme()


@TownApp.setting(section='i18n', name='domain')
def get_i18n_domain():
    return 'onegov.town'


@TownApp.setting(section='i18n', name='localedir')
def get_i18n_localedir():
    return utils.module_path('onegov.town', 'locale')


@TownApp.setting(section='i18n', name='default_locale')
def get_i18n_default_locale():
    return 'de'


@TownApp.setting(section='pages', name='type_info')
def get_pages_type_info():
    """ Defines what kind of pages are supported by onegov.town's page
    view / page editor.

    Supported properties:

        :name:
            The translatable name of the type.

        :allowed_subtypes:
            The types that may be added as children, if any.

        :form:
            The form to be used to edit the page. The form is
            expected to implement a get_content and a set_content
            method. ``get_content`` returns the page.content after
            the form has been submitted. ``set_content`` takes a page
            and sets the form fields to mirror page.content.

        :new_page_title:
            The translatable title of the new page.

        :new_page_message:
            The translatable message shown after a new page has been added.

        :edit_page_title:
            The translatable title of the edit page.

        :deletable:
            True if this type may be deleted (defaults to False).

        :delete_message:
            The translatable message shown after a page has been deleted.

        :delete_button:
            The text shown on the delete button.

        :delete_question:
            The question asked before deleting the page.

    """

    from onegov.town.views.editor import LinkForm, PageForm

    return {
        'town-root': dict(
            name=_("Topic"),
            allowed_subtypes=('page', 'link'),
            edit_page_title=_("Edit Topic"),
            form=PageForm,
            deletable=False
        ),
        'link': dict(
            name=_("Link"),
            allowed_subtypes=None,
            form=LinkForm,
            new_page_title=_("New Link"),
            new_page_message=_("Added a new link"),
            edit_page_title=_("Edit Link"),
            deletable=True,
            delete_message=_("The link was deleted"),
            delete_button=_("Delete link"),
            delete_question=_(
                "Do you really want to delete the link \"${title}\"?"),
        ),
        'page': dict(
            name=_("Topic"),
            allowed_subtypes=('page', 'link'),
            form=PageForm,
            new_page_title=_("New Topic"),
            new_page_message=_("Added a new topic"),
            edit_page_title=_("Edit Topic"),
            deletable=True,
            delete_message=_("The topic was deleted"),
            delete_button=_("Delete topic"),
            delete_question=_(
                "Do you really want to delete the topic \"${title}\"?"),
        )
    }
