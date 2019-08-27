from more.webassets import WebassetsApp


class QuillApp(WebassetsApp):
    """ Provides quill rich editor integration
    :class:`onegov.core.framework.Framework` based applications.

    """
    pass


@QuillApp.webasset_path()
def get_js_path():
    return 'assets/js'


@QuillApp.webasset_path()
def get_css_path():
    return 'assets/css'


@QuillApp.webasset('quill')
def get_leaflet_asset():
    yield 'quill.snow.css'
    yield 'custom.css'
    yield 'quill.js'
    yield 'quill.placeholder.css'
    yield 'quill.placeholder.js'
