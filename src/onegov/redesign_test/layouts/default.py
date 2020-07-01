from onegov.core.layout import ChameleonLayout


class DefaultLayout(ChameleonLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request.include('foundation-js')
