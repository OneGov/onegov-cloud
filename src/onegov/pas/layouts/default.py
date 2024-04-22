from functools import cached_property
from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


class DefaultLayout(BaseDefaultLayout):

    @cached_property
    def pas_settings_url(self) -> str:
        return self.request.link(self.app.org, 'pas-settings')
