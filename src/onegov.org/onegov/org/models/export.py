class ExportCollection(object):

    def __init__(self, app, registry='export_registry'):
        self.registry = getattr(app.config, registry)

    def by_id(self, id):
        return self.registry.get(id)

    def exports_for_current_user(self, request):
        app = request.app

        for export in self.registry.values():
            if request.has_permission(export, app.permission_by_view(export)):
                yield export


class Export(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def run(self, form, session):
        raise NotImplementedError
