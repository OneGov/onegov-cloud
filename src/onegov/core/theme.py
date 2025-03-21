""" onegov.core provides very basic theming support with the following
features:

* Themes can be external to onegov.core
* Themes can be used by onegov.core applications
* Themes can be compiled and the result is shared between applications

Themes are not meant to be switched at runtime though, they are statically
defined by the applications. The idea is to have a way to share themes
between applications, not to have powerful skinning features where the user
can change the theme at any given time.

A theme is basically a CSS file. There is no way to define images/icons
and so on. The only way to do that is to include the image in the css
file (which is not *that* crazy of an idea anyway).

To write a theme, create a class providing the properties/methods of
:class:`Theme`.

To use a theme you need to define the following setting::

    @App.setting(section='core', name='theme')
    def get_theme():
        return Theme()

To override the options passed to a theme, override the following function
in your application class::

    class App(Framework):

        @property
        def theme_options(self):
            return {'background': 'red'}

To include the theme in your html, call the following function in your
template::

    <link rel="stylesheet" type="text/css" href="${request.theme_link}">

Note that for the theme to work you need to define a filestorage. See
:meth:`onegov.core.framework.Framework.configure_application`.
"""
from __future__ import annotations

from onegov.core import __version__
from onegov.core.framework import Framework
from onegov.core import log
from onegov.core import utils
from onegov.core.filestorage import FilestorageFile


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from fs.base import FS, SubFS


class Theme:
    """ Describres a onegov.core theme.

    A onegov theme is any kind of compiled or non-compiled css file. The core
    expects a single css file that stays the same as long as the same options
    are passed to the compile function.

    Some framework based themes might required the ability to serve
    javascript at the same time. This is not done here. Such javascript
    needs to be manually included through webassets.

    This is due to the fact that onegov themes are not meant to be switched
    around. An application will chose one theme and stick with it (and
    test against it).
    """

    # this used to be configured for each theme, now it is an alias to the
    # general version and should probably not be touched
    version = __version__

    @property
    def name(self) -> str:
        """ The name of the theme, must be unique. """
        raise NotImplementedError

    @property
    def default_options(self) -> dict[str, Any]:
        """ The default options of the theme, will be overwritten by options
        passed to :meth:`compile`.

        """
        raise NotImplementedError

    def compile(self, options: dict[str, Any] | None = None) -> str:
        """ Returns a single css that represents the theme. """
        raise NotImplementedError


def get_filename(theme: Theme, options: dict[str, Any] | None = None) -> str:
    """ Returns a unique filename for the given theme and options. """

    _options = theme.default_options.copy()
    _options.update(options or {})

    return '-'.join((
        theme.name,
        theme.version,
        utils.hash_dictionary(_options),
    )) + '.css'  # needed to get the correct content_type


def compile(
    storage: FS | SubFS[FS],
    theme: Theme,
    options: dict[str, Any] | None = None,
    force: bool = False
) -> str:
    """ Generates a theme and stores it in the filestorage, returning the
    path to the theme.

    If the theme already exists and doesn't need recompiling, it will not
    compile the theme again.

    :storage:
        The Pyfilesystem storage to store the files in.

    :theme:
        The theme instance that should be compiled.

    :options:
        The hashable options passed to the theme.

    :force:
        If true, the compilation is done in any case.

    """

    filename = get_filename(theme, options)

    if not force and storage.exists(filename):
        return filename

    log.info(f'Compiling theme {theme.name}, {theme.version}')
    storage.writebytes(filename, theme.compile(options).encode('utf-8'))

    return filename


@Framework.setting(section='core', name='theme')
def get_theme() -> Theme | None:
    """ Defines the default theme, which is no theme. """
    return None


class ThemeFile(FilestorageFile):
    storage = 'themestorage'


@Framework.path(model=ThemeFile, path='/theme', absorb=True)
def get_themestorage_file(app: Framework, absorb: str) -> ThemeFile | None:
    """ Serves the theme files. """
    if app.themestorage is None:
        return None

    if app.themestorage.isfile(absorb):
        return ThemeFile(absorb)
    return None
