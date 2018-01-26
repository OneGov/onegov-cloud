from cached_property import cached_property
from onegov.org.layout import DefaultLayout
from onegov.org.new_elements import Link, Intercooler
from onegov.winterthur import _
from onegov.winterthur.collections import AddressCollection


class AddressLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Addresses"), '#'),
        ]

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return

        return [
            Link(
                text=_("Update"),
                url=self.csrf_protected_url(
                    self.request.link(self.model, '+update')
                ),
                attrs={'class': 'sync'},
                traits=Intercooler(
                    request_method='POST',
                    redirect_after=self.request.url
                )
            )
        ]


class AddressSubsetLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Addresses"), self.request.class_link(AddressCollection)),
            Link(_(self.model.street), '#')
        ]
