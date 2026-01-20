from __future__ import annotations

from more.webassets import WebassetsApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


class QuillApp(WebassetsApp):
    """ Provides quill rich editor integration
    :class:`onegov.core.framework.Framework` based applications.

    """


@QuillApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@QuillApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@QuillApp.webasset('quill')
def get_quill_asset() -> Iterator[str]:
    yield 'quill.snow.css'
    yield 'custom.css'
    yield 'quill.js'
    yield 'quill-init.js'
