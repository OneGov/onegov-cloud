from __future__ import annotations

from functools import cached_property
from onegov.core.custom import msgpack
from onegov.core.orm import orm_cached
from onegov.core.request import CoreRequest
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.org.models import News, TANAccessCollection, Topic
from onegov.page import Page, PageCollection
from onegov.user import User
from sedate import utcnow
from sqlalchemy.orm import noload


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from onegov.core.analytics import AnalyticsProvider
    from onegov.org.app import OrgApp
    from onegov.org.layout import DefaultLayout, Layout
    from onegov.ticket import Ticket


@msgpack.make_serializable(tag=20)
class PageMeta(NamedTuple):
    id: int
    type: str
    title: str
    access: str
    published: bool
    is_visible_on_homepage: bool | None
    path: str
    children: tuple[PageMeta, ...]

    def link(
        self,
        request: OrgRequest,
        variables: dict[str, Any] | None = None,
        name: str = '',
    ) -> str:
        if variables is not None:
            variables['absorb'] = self.path
        else:
            variables = {'absorb': self.path}
        return request.class_link(
            Topic if self.type == 'topic' else News,
            variables,
            name
        )


class OrgRequest(CoreRequest):

    if TYPE_CHECKING:
        app: OrgApp

    @cached_property
    def is_manager(self) -> bool:
        """ Returns true if the current user is logged in, and has the role
        editor or admin.

        """

        return self.has_role('admin', 'editor')

    def is_manager_for_model(self, model: object) -> bool:
        return self.has_permission(model, Private)

    @cached_property
    def is_admin(self) -> bool:
        """ Returns true if the current user is an admin.

        """

        return self.has_role('admin')

    @cached_property
    def is_editor(self) -> bool:
        """ Returns true if the current user is an editor.

        """

        return self.has_role('editor')

    @cached_property
    def is_supporter(self) -> bool:
        """ Returns true if the current user is a supporter.

        """

        return self.has_role('supporter')

    @cached_property
    def is_member(self) -> bool:
        """ Returns true if the current user is a member.

        """

        return self.has_role('member')

    @property
    def current_username(self) -> str | None:
        return self.identity.userid if self.identity else None

    @cached_property
    def current_user(self) -> User | None:
        if not self.identity:
            return None

        return (
            self.session.query(User)
            .filter_by(username=self.identity.userid)
            .first()
        )

    @cached_property
    def authenticated_email(self) -> str | None:
        """
        Used for granting access to private information that isn't
        necessarily tied to a registered user.
        """
        return self.browser_session.get('authenticated_email')

    @cached_property
    def first_admin_available(self) -> User | None:
        return self.session.query(User).filter_by(role='admin').order_by(
            User.created).first()

    @cached_property
    def auto_accept_user(self) -> User | None:
        username = self.app.org.auto_closing_user
        user: User | None = None
        if username:
            user = (
                self.session.query(User)
                .filter_by(username=username, role='admin')
                .first()
            )
        return user or self.first_admin_available

    @cached_property
    def email_for_new_tickets(self) -> str | None:
        return self.app.org.email_for_new_tickets

    @cached_property
    def active_mtan_session(self) -> bool:
        mtan_verified = self.browser_session.get('mtan_verified')
        if mtan_verified is None:
            return False

        session_duration = self.app.org.mtan_session_duration
        if mtan_verified + session_duration < utcnow():
            return False

        return True

    @cached_property
    def mtan_accesses(self) -> TANAccessCollection:
        return TANAccessCollection(
            self.session,
            session_id=self.browser_session.mtan_number,
            access_window=self.app.org.mtan_access_window
        )

    @cached_property
    def mtan_access_limit_exceeded(self) -> bool:
        limit = self.app.org.mtan_access_window_requests
        if limit is None:
            # no limit so we can't exceed it
            return False

        # if we're below the limit we're fine
        if self.mtan_accesses.count() < limit:
            return False

        # if we already accessed this url we are also still fine
        return self.mtan_accesses.by_url(self.path_url) is None

    def auto_accept(self, ticket: Ticket) -> bool:
        if self.app.org.ticket_auto_accept_style == 'role':
            roles = self.app.org.ticket_auto_accept_roles
            if not roles:
                return False
            return self.has_role(*roles)
        return ticket.handler_code in (self.app.org.ticket_auto_accepts or ())

    @orm_cached(policy='on-table-change:pages', by_role=True)
    def pages_tree(self) -> tuple[PageMeta, ...]:
        """
        This is the entire pages tree preloaded into the individual
        parent/children attributes. We optimize this as much as possible
        by performing the recursive join in Python, rather than SQL.

        """
        query = PageCollection(self.session).query(ordered=False)
        query = query.options(
            # we populate these relationship ourselves
            noload(Page.parent),
            noload(Page.children),
        )
        query = query.order_by(Page.order)

        # first we build a map from parent_ids to their children
        parent_to_child: dict[int | None, list[Page]] = {}
        for page in query:
            parent_to_child.setdefault(page.parent_id, []).append(page)

        def extend_path(page: Page, path: str | None) -> str:
            if page.type == 'news' and path is None:
                # the root news page is not part of the path
                return ''
            return f'{path}/{page.name}' if path else page.name

        def generate_subtree(
            parent_id: int | None,
            path: str | None
        ) -> tuple[PageMeta, ...]:
            return tuple(
                PageMeta(
                    id=page.id,
                    type=page.type,
                    title=page.title,
                    access=page.meta.get('access', 'public'),
                    published=published,
                    path=(subpath := extend_path(page, path)),
                    is_visible_on_homepage=page.meta.get('is_visible_on_homepage'),
                    children=tuple(generate_subtree(page.id, subpath))
                )
                for page in parent_to_child.get(parent_id, ())
                if self.is_visible(page)
                if (published := getattr(page, 'published', True))
                or self.is_manager
            )

        # we return the root pages which should contain references to all
        # the child pages
        return generate_subtree(None, None)

    @orm_cached(policy='on-table-change:pages', by_role=True)
    def root_pages(self) -> tuple[PageMeta, ...]:

        def include(page: PageMeta) -> bool:
            if page.type != 'news':
                return True

            return True if page.children else False

        return tuple(p for p in self.pages_tree if include(p))

    @orm_cached(policy='on-table-change:pages', by_role=True)
    def homepage_pages(self) -> dict[int, list[PageMeta]]:

        def visit_topics(
            pages: Iterable[PageMeta],
            root_id: int | None = None
        ) -> Generator[tuple[int, PageMeta]]:
            for page in pages:
                if page.type != 'topic':
                    continue

                if root_id is not None and page.is_visible_on_homepage:
                    yield root_id, page

                yield from visit_topics(
                    page.children,
                    root_id=root_id or page.id
                )

        result: dict[int, list[PageMeta]] = {}
        for root_id, meta in visit_topics(self.root_pages):
            result.setdefault(root_id, []).append(meta)

        for topics in result.values():
            topics.sort(
                key=lambda p: normalize_for_url(p.title)
            )

        return result

    @property
    def analytics_provider(self) -> AnalyticsProvider | None:
        """ Returns the active analytics provider. """
        if name := self.app.org.analytics_provider_name:
            return self.app.available_analytics_providers.get(name)
        return None

    def get_layout(self, model: object) -> Layout | DefaultLayout:
        """
        Get the registered layout for a model instance.
        """
        layout_class = self.app.get_layout_class(model)

        # if layout_class is None:
        #     layout_class = DefaultLayout
        assert layout_class is not None

        return layout_class(model, self)
