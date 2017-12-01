from cached_property import cached_property
from onegov.ballot import ElectionCollection
from onegov.ballot import VoteCollection
from onegov.election_day import _
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.layouts.default import DefaultLayout


class ManageLayout(DefaultLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(self.model)

    @cached_property
    def menu(self):
        menu = []
        session = self.request.app.session()

        link = self.request.link(VoteCollection(session))
        class_ = 'active' if link == self.manage_model_link else ''
        menu.append((_("Votes"), link, class_))

        link = self.request.link(ElectionCollection(session))
        class_ = 'active' if link == self.manage_model_link else ''
        menu.append((_("Elections"), link, class_))

        if self.principal.wabsti_import:
            link = self.request.link(DataSourceCollection(session))
            active = (
                link == self.manage_model_link or
                isinstance(self.model, DataSourceItemCollection)
            )
            class_ = 'active' if active else ''
            menu.append((_("Data sources"), link, class_))

        if self.principal.sms_notification:
            link = self.request.link(SubscriberCollection(session))
            class_ = 'active' if link == self.manage_model_link else ''
            menu.append((_("Subscribers"), link, class_))

        return menu

    def title(self):
        try:
            return self.breadcrumbs[-1][0]
        except (IndexError, TypeError):
            return ''

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('backend_common')
        self.breadcrumbs = [
            (_("Manage"), super().manage_link, 'unavailable'),
        ]


class ManageElectionsLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            ElectionCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Elections"), request.link(self.model), '')
        )


class ManageVotessLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            VoteCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Votes"), request.link(self.model), ''),
        )


class ManageSubscribersLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            SubscriberCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Subscribers"), request.link(self.model), ''),
        )


class ManageDataSourcesLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            DataSourceCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Data sources"), request.link(self.model), ''),
        )


class ManageDataSourceItemsLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            DataSourceItemCollection(
                self.request.app.session(),
                self.model.id
            )
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (
                _("Data sources"),
                self.request.link(
                    DataSourceCollection(self.request.app.session())
                ),
                ''
            ),
        )
        self.breadcrumbs.append(
            (_("Mappings"), request.link(self.model), ''),
        )
