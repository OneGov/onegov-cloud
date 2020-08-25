from onegov.org.layout import DefaultLayout as BaseLayout


class DefaultLayout(BaseLayout):

    def instance_link(self, instance):
        return self.request.link(instance)
