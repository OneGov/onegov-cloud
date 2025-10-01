from __future__ import annotations

from functools import cached_property
from onegov.activity import Activity, ActivityCollection, Occasion
from onegov.activity import PublicationRequestCollection
from onegov.activity.models import DAYS
from onegov.core.templates import render_macro
from onegov.feriennet import _
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.ticket import OrgTicketMixin
from onegov.search import SearchableContent
from onegov.ticket import handlers, Handler, Ticket


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from markupsafe import Markup
    from onegov.activity.models import PublicationRequest
    from onegov.feriennet.request import FeriennetRequest


class VacationActivity(Activity, CoordinatesExtension, SearchableContent):

    __mapper_args__ = {'polymorphic_identity': 'vacation'}

    es_type_name = 'vacation'

    es_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
        'lead': {'type': 'localized', 'weight': 'B'},
        'text': {'type': 'localized_html', 'weight': 'C'},
        # FIXME: We may want to split this into more properties
        #        the organiser's name definitely seems more important
        #        than their bank account or emergency contact for searching
        'organiser_text': {'type': 'text', 'weight': 'B'}
    }

    @property
    def es_public(self) -> bool:
        return self.state == 'accepted'

    @property
    def es_skip(self) -> bool:
        return self.state == 'preview'

    @property
    def organiser(self) -> list[str]:
        organiser: list[str] = [
            self.user.username,
            # FIXME: For now we assume this is always set, if it
            #        is sometimes not set, then perhaps we should
            #        only append it when it is set.
            self.user.realname  # type:ignore[list-item]
        ]

        userprofile_keys = (
            'organisation',
            'address',
            'zip_code',
            'place',
            'email',
            'phone',
            'emergency',
            'website',
            'bank_account',
            'bank_beneficiary',
        )

        for key in userprofile_keys:
            if not self.user.data:
                continue
            if value := self.user.data.get(key):
                organiser.append(value)

        return organiser

    @property
    def organiser_text(self) -> str:
        return ' '.join(self.organiser)

    def ordered_tags(
        self,
        request: FeriennetRequest,
        durations: int | None = None
    ) -> list[str]:

        tags = [request.translate(_(tag)) for tag in self.tags]

        if durations is None:
            period = request.app.active_period
            durations = sum(o.duration for o in (
                request.session.query(Occasion)
                .with_entities(Occasion.duration)
                .distinct()
                .filter_by(activity_id=self.id)
                .filter_by(period_id=period.id if period else None)
            ))

        if DAYS.has(durations, DAYS.half):
            tags.append(request.translate(_('Half day')))
        if DAYS.has(durations, DAYS.full):
            tags.append(request.translate(_('Full day')))
        if DAYS.has(durations, DAYS.many):
            tags.append(request.translate(_('Multiple days')))

        return sorted(tags)


class ActivityTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FER'}  # type:ignore
    es_type_name = 'activity_tickets'

    def reference_group(
        self,
        request: FeriennetRequest  # type:ignore[override]
    ) -> str:
        return self.handler.title


@handlers.registered_handler('FER')
class VacationActivityHandler(Handler):

    handler_title = _('Activities')
    code_title = _('Activities')

    @cached_property
    def collection(self) -> PublicationRequestCollection:
        return PublicationRequestCollection(self.session)

    @cached_property
    def activity(self) -> Activity | None:
        if self.publication_request is None:
            return None
        return self.publication_request.activity

    @cached_property
    def publication_request(self) -> PublicationRequest | None:
        return self.collection.by_id(self.id)

    @property
    def deleted(self) -> bool:
        return self.publication_request is None

    @property
    def email(self) -> str:
        return self.activity.username if self.activity else ''

    @property
    def title(self) -> str:
        return self.activity.title if self.activity else ''

    @property
    def subtitle(self) -> str | None:
        if self.publication_request is None:
            return None
        return self.publication_request.period.title

    @property
    def group(self) -> str:
        return _('Activity')

    @property
    def extra_data(self) -> Sequence[str]:
        return ()

    @property
    def undecided(self) -> bool:
        if self.deleted:
            return False

        assert self.activity is not None
        return self.activity.state == 'proposed'

    @cached_property
    def ticket_deletable(self) -> bool:
        if super().ticket_deletable:
            if self.activity is not None:
                return self.activity.state != 'archived'
            return True
        return False

    def get_summary(
        self,
        request: FeriennetRequest  # type:ignore[override]
    ) -> Markup:

        assert self.publication_request is not None
        assert self.activity is not None
        from onegov.feriennet.layout import DefaultLayout
        layout = DefaultLayout(self.activity, request)

        ac = ActivityCollection(request.session)
        activities = ac.by_username(self.activity.username)

        return render_macro(
            layout.macros['activity_ticket_summary'], request, {
                'activity': self.activity,
                'layout': layout,
                'show_ticket_panel': False,
                'ticket': self.ticket,
                'is_first': activities.count() == 1,
                'period': self.publication_request.period
            }
        )

    def get_period_bound_links(
        self,
        request: FeriennetRequest
    ) -> Iterator[Link]:

        if self.activity is None:
            return

        if self.activity.state in ('proposed', 'archived'):
            yield Link(
                text=_('Publish'),
                url=request.link(self.activity, name='accept'),
                attrs={'class': 'accept-activity'},
                traits=(
                    Confirm(
                        _('Do you really want to publish this activity?'),
                        _('This cannot be undone.'),
                        _('Publish Activity'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.url
                    )
                )
            )

        if self.activity.state == 'accepted':
            yield Link(
                text=_('Archive'),
                url=request.link(self.activity, name='archive'),
                attrs={'class': 'archive-activity'},
                traits=(
                    Confirm(
                        _('Do you really want to archive this activity?'),
                        _(
                            'The activity will be made private as a result.'
                        ),
                        _('Archive Activity'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.url
                    )
                )
            )

    def get_links(  # type:ignore[override]
        self,
        request: FeriennetRequest  # type:ignore[override]
    ) -> list[Link]:

        links = list(self.get_period_bound_links(request))
        links.append(Link(
            text=_('Show activity'),
            url=request.return_here(request.link(self.activity)),
            attrs={'class': 'show-activity'}
        ))

        return links
