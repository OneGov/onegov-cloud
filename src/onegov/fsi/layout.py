from onegov.org.layout import DefaultLayout as OrgDefaultLayout
from onegov.org.layout import Layout as OrgBaseLayout


class Layout(OrgBaseLayout):
    pass


class DefaultLayout(OrgDefaultLayout):

    def include_editor(self):
        self.request.include('redactor')
        self.request.include('editor')

    def instance_link(self, instance):
        return self.request.link(instance)
