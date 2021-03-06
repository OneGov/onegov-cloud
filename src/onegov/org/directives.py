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


class UserlinkAction(Action):
    """ Registers a user link group. """

    config = {
        'linkgroup_registry': list
    }

    counter = iter(range(1, 123456789))

    def __init__(self):
        self.name = next(self.counter)

    def identifier(self, linkgroup_registry):
        return self.name

    def perform(self, func, linkgroup_registry):
        linkgroup_registry.append(func)


class DirectorySearchWidgetAction(Action):
    """ Registers a directory search widget. """

    config = {
        'directory_search_widget_registry': dict
    }

    def __init__(self, name):
        self.name = name

    def identifier(self, directory_search_widget_registry):
        return self.name

    def perform(self, cls, directory_search_widget_registry):
        cls.name = self.name

        assert hasattr(cls, 'html')
        assert hasattr(cls, 'adapt')

        directory_search_widget_registry[self.name] = cls


class SettingsView(Action):
    """ Registers a settings view. """

    config = {
        'settings_view_registry': dict
    }

    def __init__(self, name, title, order=0, icon='fa-cogs'):
        self.name = name
        self.setting = {
            'name': name,
            'title': title,
            'order': order,
            'icon': icon
        }

    def identifier(self, settings_view_registry):
        return self.name

    def perform(self, func, settings_view_registry):
        settings_view_registry[self.name] = self.setting


class Boardlet(Action):
    """ Registers a boardlet on the Dashboard. """

    config = {
        'boardlets_registry': dict
    }

    def __init__(self, name, order):
        assert isinstance(order, tuple) and len(order) == 2, """
            The order should consist of two values, a group and an order
            within the group.
        """

        self.name = name
        self.order = order

    def identifier(self, boardlets_registry):
        return self.name

    def perform(self, func, boardlets_registry):
        boardlets_registry[self.name] = {
            'cls': func,
            'order': self.order
        }
