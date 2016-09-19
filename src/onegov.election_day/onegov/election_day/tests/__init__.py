
class DummyPrincipal(object):
    name = 'name'


class DummyApp(object):
    principal = DummyPrincipal()


class DummyRequest(object):

    def link(self, model, name=''):
        return '{}/{}'.format(
            model.__class__.__name__, name or getattr(model, 'id', 'archive')
        )

    @property
    def app(self):
        return DummyApp()
