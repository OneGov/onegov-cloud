from onegov.core.layout import ChameleonLayout


class Layout(ChameleonLayout):

    def __init__(self, request, model):
        super(Layout, self).__init__(request, model)
        self.request.include('common')


class DefaultLayout(Layout):
    pass
