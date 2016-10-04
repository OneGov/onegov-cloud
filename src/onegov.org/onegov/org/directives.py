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
