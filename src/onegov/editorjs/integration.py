from more.webassets import WebassetsApp


class EditorJsApp(WebassetsApp):
    pass


@EditorJsApp.webasset_path()
def get_js_path():
    return 'assets/js'
