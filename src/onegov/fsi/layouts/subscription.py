from __future__ import annotations

from functools import cached_property

from onegov.core.elements import Link, Confirm, Intercooler, LinkGroup
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseEvent, CourseSubscription


class SubscriptionCollectionLayout(DefaultLayout):

    model: SubscriptionsCollection

    @property
    def for_himself(self) -> bool:
        return self.model.attendee_id == self.request.attendee_id

    def link(self, subscription: CourseSubscription) -> str:
        if subscription.is_placeholder:
            return self.request.link(subscription, name='edit-placeholder')
        return self.request.link(subscription.attendee)

    def confirmation_link(self, subscription: CourseSubscription) -> str:
        return self.csrf_protected_url(
            self.request.link(subscription, name='toggle-confirm'))

    @cached_property
    def title(self) -> str:
        if self.request.view_name == 'add':
            return _('Add Attendee')
        if self.request.view_name == 'add-placeholder':
            return _('Add Placeholder')
        if self.model.course_event_id:
            assert self.course_event is not None
            return _('Attendees Event ${event} - ${date} - ${begin}',
                     mapping={'event': self.course_event.name,
                              'date': self.format_date(
                                  self.course_event.start, 'date'),
                              'begin': self.format_date(
                                  self.course_event.start, 'time'
                              )})
        if self.for_himself:
            return _('My Event Subscriptions')
        elif self.model.attendee_id:
            return _('All event subscriptions for ${attendee}',
                     mapping={'attendee': self.model.attendee})
        return _('All Event Subscriptions')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        if not self.request.view_name:
            links.append(
                Link(
                    text=_('PDF'),
                    url=self.request.link(self.model, name='pdf'),
                    attrs={
                        'class': 'print-icon',
                        'target': '_blank'
                    }
                )
            )
        if not self.request.is_manager:
            return links

        add_links = [
            Link(
                _('Subscription'),
                self.request.link(self.model, name='add'),
                attrs={'class': 'add-icon'}
            )
        ]

        if self.request.is_admin:
            add_links.append(
                Link(
                    _('Placeholder'),
                    self.request.link(self.model, name='add-placeholder'),
                    attrs={'class': 'add-icon'}
                )
            )
            if self.model.course_event_id:
                if self.show_send_info_mail_button:
                    links.append(
                        Link(
                            _('Send Info Mail'),
                            self.preview_info_mail_url,
                            attrs={'class': 'email-link'}
                        )
                    )

        links.append(
            LinkGroup(
                title=_('Add'),
                links=add_links
            )
        )

        return links

    @cached_property
    def course_event(self) -> CourseEvent | None:
        return self.model.course_event

    @cached_property
    def preview_info_mail_url(self) -> str:
        assert self.course_event is not None
        return self.request.link(
            self.course_event.info_template, name='send')

    @cached_property
    def show_send_info_mail_button(self) -> bool:
        return self.course_event is not None and not self.course_event.is_past

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        if self.model.course_event_id:
            assert self.course_event is not None
            links.append(
                Link(
                    self.course_event.name,
                    self.request.link(self.model.course_event)
                )
            )
        links.append(
            Link(_('Course Subscriptions'), self.request.link(self.model))
        )
        if self.request.view_name in ('add', 'add-placeholder'):
            links.append(Link(_('Add')))
        if self.model.course_event_id:
            assert self.course_event is not None
            links.append(
                Link(
                    self.format_date(self.course_event.start, 'date_long'),
                    self.request.link(self.course_event))
            )
        return links

    def intercooler_btn_for_item(
        self,
        subscription: CourseSubscription
    ) -> Link:

        confirm = subscription.is_placeholder and Confirm(
            _('Do you want to delete the placeholder ?'),
            yes=_('Delete'),
            no=_('Cancel')
        ) or Confirm(
            _('Do you want to cancel the subscription ?'),
            _('A confirmation email will be sent to the person.'),
            _('Cancel subscription for course event'),
            _('Cancel')
        )

        return Link(
            text=_('Delete'),
            url=self.csrf_protected_url(
                self.request.link(subscription)
            ),
            attrs={'class': 'button tiny alert'},
            traits=(
                confirm,
                Intercooler(
                    request_method='DELETE',
                    redirect_after=self.request.link(self.model)
                )
            )
        )


class SubscriptionLayout(DefaultLayout):
    """ Only used for editing since it does not contain fields """

    model: CourseSubscription

    @cached_property
    def collection(self) -> SubscriptionsCollection:
        return SubscriptionsCollection(
            self.request.session,
            auth_attendee=self.request.attendee,
            attendee_id=None,
            course_event_id=self.model.course_event_id
        )

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if not self.request.is_admin:
            return []
        return [
            Link(
                text=_('Delete'),
                url=self.csrf_protected_url(
                    self.request.link(self.model)
                ),
                attrs={'class': 'button tiny alert'},
                traits=(
                    Confirm(
                        _('Do you want to cancel the subscription ?'),
                        _(
                            'A confirmation email will be sent to you later.'),
                        _('Cancel subscription for course event'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(self.model)
                    )
                )
            )
        ]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                self.model.course_event.name,
                self.request.link(self.model.course_event)
            )
        )
        links.append(
            Link(_('Course Subscriptions'), self.request.link(self.collection))
        )
        links.append(Link(str(self.model)))
        return links
