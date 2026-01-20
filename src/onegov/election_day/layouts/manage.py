from __future__ import annotations

from functools import cached_property
from onegov.election_day import _
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import ElectionCollection
from onegov.election_day.collections import ElectionCompoundCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.collections import VoteCollection
from onegov.election_day.layouts.default import DefaultLayout
from onegov.election_day.layouts.election import ElectionLayout
from onegov.election_day.layouts.election_compound import (
    ElectionCompoundLayout)
from onegov.election_day.layouts.vote import VoteLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import EmailSubscriber
from onegov.election_day.models import SmsSubscriber
from onegov.election_day.models import Vote
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.election_day.models import DataSource
    from onegov.election_day.models import Subscriber
    from onegov.election_day.models import UploadToken
    from onegov.election_day.request import ElectionDayRequest

    from .election import NestedMenu


class ManageLayout(DefaultLayout):

    def __init__(self, model: Any, request: ElectionDayRequest):
        super().__init__(model, request)
        self.request.include('backend_common')
        self.request.include('chosen')
        self.breadcrumbs = [
            (_('Manage'), super().manage_link, 'unavailable'),
        ]

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(self.model)

    @cached_property
    def menu(self) -> NestedMenu:
        session = self.request.session
        principal = self.principal

        result: NestedMenu = []
        result.append((
            _('Votes'),
            self.request.link(VoteCollection(session)),
            isinstance(self.model, VoteCollection),
            []
        ))

        if principal.domain == 'municipality':
            result.append((
                _('Elections'),
                self.request.link(ElectionCollection(session)),
                isinstance(self.model, ElectionCollection),
                []
            ))
        else:
            submenu: NestedMenu = []
            submenu.append((
                _('Elections'),
                self.request.link(ElectionCollection(session)),
                isinstance(self.model, ElectionCollection),
                []
            ))

            submenu.append((
                _('Compounds of elections'),
                self.request.link(ElectionCompoundCollection(session)),
                isinstance(self.model, ElectionCompoundCollection),
                []
            ))
            result.append((
                _('Elections'),
                '',
                isinstance(self.model, (
                    ElectionCollection,
                    ElectionCompoundCollection
                )),
                submenu
            ))

        submenu = []
        submenu.append((
            _('Upload tokens'),
            self.request.link(UploadTokenCollection(session)),
            isinstance(self.model, UploadTokenCollection),
            []
        ))
        if principal.wabsti_import:
            submenu.append((
                _('Wabsti data sources'),
                self.request.link(DataSourceCollection(session)),
                isinstance(self.model, (
                    DataSourceCollection,
                    DataSourceItemCollection
                )),
                []
            ))
        result.append((
            _('Import configuration'),
            '',
            isinstance(self.model, (
                UploadTokenCollection,
                DataSourceCollection,
                DataSourceItemCollection
            )),
            submenu
        ))

        submenu = []
        if principal.sms_notification:
            submenu.append((
                _('SMS subscribers'),
                self.request.link(SmsSubscriberCollection(session)),
                isinstance(self.model, SmsSubscriberCollection),
                []
            ))
        if self.principal.email_notification:
            submenu.append((
                _('Email subscribers'),
                self.request.link(EmailSubscriberCollection(session)),
                isinstance(self.model, EmailSubscriberCollection),
                []
            ))
        submenu.append((
            _('Trigger notifications'),
            self.request.link(
                self.principal, name='trigger-notifications'
            ),
            'trigger-notifications' in self.request.url,
            []
        ))
        result.append((
            _('Notifications'),
            '',
            isinstance(self.model, (
                SmsSubscriberCollection,
                EmailSubscriberCollection
            )),
            submenu
        ))

        result.append((
            _('Screens'),
            self.request.link(ScreenCollection(session)),
            isinstance(self.model, ScreenCollection),
            []
        ))

        if self.request.is_secret(self.model):
            submenu = [
                (
                    _('Update archived results'),
                    self.request.link(self.principal, 'update-results'),
                    'update-results' in self.request.url,
                    []
                ),
                (
                    _('Clear cache'),
                    self.request.link(self.principal, 'clear-cache'),
                    'clear-cache' in self.request.url,
                    []
                )
            ]

            result.append((
                _('Administration'),
                '',
                False,
                submenu
            ))

        return result

    def title(self) -> str:
        try:
            return self.breadcrumbs[-1][0]
        except (IndexError, TypeError):
            return ''

    def clear_media(
        self,
        tabs: Collection[str] | None = None,
        additional: list[str] | None = None
    ) -> int:

        tabs = tabs or []
        additional = additional or []
        app = self.request.app
        filestorage = app.filestorage
        assert filestorage is not None
        paths = additional.copy()
        paths.extend(
            'pdf/{}'.format(pdf_filename(self.model, locale))
            for locale in app.locales
        )
        paths.extend(
            'svg/{}'.format(svg_filename(self.model, tab, locale))
            for tab in tabs
            for locale in app.locales
        )
        count = 0
        for path in paths:
            if filestorage.exists(path):
                filestorage.remove(path)
                count += 1
        return count


class ManageElectionsLayout(ManageLayout):

    model: Election | ElectionCollection

    def __init__(
        self,
        model: Election | ElectionCollection,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Elections'), request.link(self.model), '')
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            ElectionCollection(self.request.session)
        )

    def clear_media(self) -> int:  # type:ignore[override]
        if isinstance(self.model, Election):
            layout = ElectionLayout(self.model, self.request)
            return super().clear_media(tabs=layout.all_tabs)
        return 0


class ManageElectionCompoundsLayout(ManageLayout):

    model: ElectionCompound | ElectionCompoundCollection

    def __init__(
        self,
        model: ElectionCompound | ElectionCompoundCollection,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Compounds of elections'), request.link(self.model), '')
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            ElectionCompoundCollection(self.request.session)
        )

    def clear_media(self) -> int:  # type:ignore[override]
        if isinstance(self.model, ElectionCompound):
            layout = ElectionCompoundLayout(self.model, self.request)
            return super().clear_media(tabs=layout.all_tabs)
        return 0


class ManageVotesLayout(ManageLayout):

    model: Vote | VoteCollection

    def __init__(
        self,
        model: Vote | VoteCollection,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Votes'), request.link(self.model), ''),
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            VoteCollection(self.request.session)
        )

    def clear_media(self) -> int:  # type:ignore[override]
        if isinstance(self.model, Vote):
            layout = VoteLayout(self.model, self.request)
            additional = [
                'svg/{}'.format(svg_filename(ballot, prefix, locale))
                for ballot in self.model.ballots
                for prefix in ('entities-map', 'districts-map')
                for locale in self.request.app.locales
            ]
            return super().clear_media(
                tabs=layout.all_tabs,
                additional=additional
            )
        return 0


class ManageSubscribersLayout(ManageLayout):

    model: SubscriberCollection[Any] | Subscriber

    def __init__(
        self,
        model: SubscriberCollection[Any] | Subscriber,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        if isinstance(self.model, EmailSubscriberCollection):
            self.breadcrumbs.append(
                (_('Email subscribers'), request.link(self.model), ''),
            )
        elif isinstance(self.model, SmsSubscriberCollection):
            self.breadcrumbs.append(
                (_('SMS subscribers'), request.link(self.model), ''),
            )
        else:
            self.breadcrumbs.append(
                (_('Subscribers'), request.link(self.model), ''),
            )

    @cached_property
    def manage_model_link(self) -> str:
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


class ManageUploadTokensLayout(ManageLayout):

    model: UploadToken | UploadTokenCollection

    def __init__(
        self,
        model: UploadToken | UploadTokenCollection,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Upload tokens'), request.link(self.model), ''),
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            UploadTokenCollection(self.request.session)
        )


class ManageDataSourcesLayout(ManageLayout):

    def __init__(self, model: Any, request: ElectionDayRequest) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Wabsti data sources'), request.link(self.model), ''),
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            DataSourceCollection(self.request.session)
        )


class ManageDataSourceItemsLayout(ManageLayout):

    model: DataSource | DataSourceItemCollection

    def __init__(
        self,
        model: DataSource | DataSourceItemCollection,
        request: ElectionDayRequest
    ) -> None:

        super().__init__(model, request)
        self.breadcrumbs.append(
            (
                _('Wabsti data sources'),
                self.request.link(
                    DataSourceCollection(self.request.session)
                ),
                ''
            ),
        )
        self.breadcrumbs.append(
            (_('Mappings'), request.link(self.model), ''),
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            DataSourceItemCollection(
                self.request.session,
                self.model.id
            )
        )


class ManageScreensLayout(ManageLayout):

    def __init__(self, model: Any, request: ElectionDayRequest) -> None:
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_('Screens'), request.link(self.model), ''),
        )

    @cached_property
    def manage_model_link(self) -> str:
        return self.request.link(
            ScreenCollection(self.request.session)
        )
