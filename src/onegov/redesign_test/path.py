from onegov.redesign_test.app import RedesignApp
from onegov.redesign_test.layouts.default import DefaultLayout


class SomeModel:
    pass


@RedesignApp.path(
    model=SomeModel,
    path='/'
)
def get_some_model(app):
    return SomeModel()


@RedesignApp.html(
    model=SomeModel,
    template='homepage.pt'
)
def get_homepage(self, request):
    return {'layout': DefaultLayout(self, request)}
