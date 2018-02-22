from cached_property import cached_property
from onegov.ballot import ElectionCollection
from onegov.ballot import VoteCollection
from onegov.election_day import _
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.layouts.default import DefaultLayout
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber


class ManageLayout(DefaultLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(self.model)

    @cached_property
    def menu(self):
        menu = []
        session = self.request.session

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
            link = self.request.link(SmsSubscriberCollection(session))
            class_ = 'active' if link == self.manage_model_link else ''
            menu.append((_("SMS subscribers"), link, class_))

        if self.principal.email_notification:
            link = self.request.link(EmailSubscriberCollection(session))
            class_ = 'active' if link == self.manage_model_link else ''
            menu.append((_("Email subscribers"), link, class_))

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
            ElectionCollection(self.request.session)
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Elections"), request.link(self.model), '')
        )


class ManageVotesLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            VoteCollection(self.request.session)
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Votes"), request.link(self.model), ''),
        )


class ManageSubscribersLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        if isinstance(self.model, SubscriberCollection):
            return self.request.link(self.model)

        if isinstance(self.model, SmsSubscriber):
            return self.request.link(
                SmsSubscriberCollection(self.request.session)
            )
        elif isinstance(self.model, EmailSubscriber):
            return self.request.link(
                EmailSubscriberCollection(self.request.session)
            )

        raise NotImplementedError()

    def __init__(self, model, request):
        super().__init__(model, request)
        if isinstance(self.model, EmailSubscriberCollection):
            self.breadcrumbs.append(
                (_("Email subscribers"), request.link(self.model), ''),
            )
        elif isinstance(self.model, SmsSubscriberCollection):
            self.breadcrumbs.append(
                (_("SMS subscribers"), request.link(self.model), ''),
            )
        else:
            self.breadcrumbs.append(
                (_("Subscribers"), request.link(self.model), ''),
            )


class ManageDataSourcesLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            DataSourceCollection(self.request.session)
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
                self.request.session,
                self.model.id
            )
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (
                _("Data sources"),
                self.request.link(
                    DataSourceCollection(self.request.session)
                ),
                ''
            ),
        )
        self.breadcrumbs.append(
            (_("Mappings"), request.link(self.model), ''),
        )
