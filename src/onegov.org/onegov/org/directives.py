from dectate import Action


class HomepageWidgetAction(Action):
    """ Register a cronjob. """

    config = {
        'homepage_widget_registry': dict
    }

    def __init__(self, tag):
        self.tag = tag

    def identifier(self, homepage_widget_registry):
        return self.tag

    def perform(self, func, homepage_widget_registry):
        widget = func()
        widget.tag = self.tag  # keep redundantly for ease of access

        homepage_widget_registry[self.tag] = widget


class ExportAction(Action):
    """ Register an export. """

    config = {
        'export_registry': dict
    }

    def __init__(self, id, **kwargs):
        self.id = id
        self.kwargs = kwargs
        self.kwargs['id'] = id

    def identifier(self, export_registry):
        return self.id

    def perform(self, cls, export_registry):
        export_registry[self.id] = cls(**self.kwargs)
