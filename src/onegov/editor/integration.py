from more.webassets import WebassetsApp


class EditorApp(WebassetsApp):
    """ Provides quill rich editor integration
    :class:`onegov.core.framework.Framework` based applications.

    """
    pass


@EditorApp.webasset_path()
def get_js_path():
    return 'assets/js'


@EditorApp.webasset('tiptap')
def get_tiptap_asset():
    yield 'tiptap.bundle.min.js'
    yield 'tiptap.init.js'
