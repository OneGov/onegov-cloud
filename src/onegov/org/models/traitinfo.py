from __future__ import annotations
import json

from onegov.org import _
from onegov.org.elements import DeleteLink, Link, LinkGroup, IFrameLink
from onegov.org.models import Organisation
from onegov.org.models.clipboard import Clipboard
from onegov.org.models.editor import Editor
from onegov.page import Page


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from onegov.core.elements import Link as BaseLink
    from onegov.form import Form
    from onegov.org.request import OrgRequest
    from sqlalchemy import Column


#: Contains the messages that differ for each trait (the handling of all traits
#: is the same). New traits need to adapt the same messages as the others.
TRAIT_MESSAGES: dict[str, dict[str, str]] = {
    'link': {
        'name': _('Link'),
        'new_page_title': _('New Link'),
        'new_page_added': _('Added a new link'),
        'edit_page_title': _('Edit Link'),
        'move_page_title': _('Move Link'),
        'delete_message': _('The link was deleted'),
        'delete_button': _('Delete link'),
        'delete_question': _(
            'Do you really want to delete the link "${title}"?'),
    },
    'page': {
        'name': _('Topic'),
        'new_page_title': _('New Topic'),
        'new_page_added': _('Added a new topic'),
        'edit_page_title': _('Edit Topic'),
        'move_page_title': _('Move Topic'),
        'delete_message': _('The topic was deleted'),
        'delete_button': _('Delete topic'),
        'delete_question': _(
            'Do you really want to delete the topic "${title}"?'),
    },
    'news': {
        'name': _('News'),
        'new_page_title': _('Add News'),
        'new_page_added': _('Added news'),
        'edit_page_title': _('Edit News'),
        'delete_message': _('The news was deleted'),
        'delete_button': _('Delete news'),
        'delete_question': _(
            'Do you really want to delete the news "${title}"?'),
    },
    'iframe': {
        'name': _('iFrame'),
        'new_page_title': _('Add iFrame'),
        'new_page_added': _('Added iFrame'),
        'edit_page_title': _('Edit iFrame'),
        'move_page_title': _('Move iFrame'),
        'delete_message': _('The iFrame was deleted'),
        'delete_button': _('Delete iFrame'),
        'delete_question': _(
            'Do you really want to delete the iFrame "${title}"?'),
    }
}


class TraitInfo:
    """" Typically used as a mixin for adjacency list based models,
    this class provides access to the trait related methods.

    Traits are like subtypes of models. For example, the Page model has
    a page trait and a link trait. Both are managed under the same tree as
    the same type (Page), but one is rendered as a redirect, the other as
    a normal page.

    """

    if TYPE_CHECKING:
        # forward declare Page attributes we rely on
        title: Column[str]
        meta: Column[dict[str, Any]]

        @property
        def editable(self) -> bool: ...
        @property
        def deletable(self) -> bool: ...
        @property
        def url_changeable(self) -> bool: ...

    @property
    def trait(self) -> str | None:
        """ Gets the trait of the page. """
        return self.meta.get('trait')

    @trait.setter
    def trait(self, trait: str | None) -> None:
        """ Sets the trait of the page. """
        self.meta['trait'] = trait

    @property
    def trait_messages(self) -> dict[str, dict[str, str]]:
        """ Returns all trait_messages. """
        return TRAIT_MESSAGES

    @property
    def allowed_subtraits(self) -> Sequence[str]:
        """ Returns a list of traits that this page may contain. """
        raise NotImplementedError

    @property
    def paste_target(self) -> TraitInfo:
        """ Returns the page that should be used as parent for the content
        pasting if paste is called on the current page (self).

        This is usually just self. If the paste action should put the content
        alongside the current page, it would be the parent.

        """
        raise NotImplementedError

    def is_supported_trait(self, trait: str) -> bool:
        """ Returns true if the given trait is supported by this type This
        doesn't mean that the trait may be added to this page, it serves
        as a simple sanity check, returning True if the combination of the
        type and the trait make any sense at all.

        """
        raise NotImplementedError

    def get_form_class(
        self,
        trait: str,
        action: str,
        request: OrgRequest
    ) -> type[Form]:
        """ Returns the form class for the given trait, action. """
        raise NotImplementedError

    def get_editbar_links(
        self,
        request: OrgRequest
    ) -> Sequence[BaseLink | LinkGroup]:
        """ Returns the editbar links on the private view of this trait. """
        links = list(self.get_edit_links(request))
        links.append(
            LinkGroup(
                title=_('Add'),
                links=tuple(self.get_add_links(request))
            )
        )

        return links

    def get_add_links(
        self,
        request: OrgRequest
    ) -> Iterator[BaseLink]:
        """ Yields the add links shown on the private view of this trait. """

        for trait in self.allowed_subtraits:

            name = self.trait_messages[trait]['name']

            yield Link(
                name,
                request.link(Editor('new', self, trait)),
                classes=(
                    f'new-{trait}',
                    'show-new-content-placeholder'
                )
            )

    def get_edit_links(
        self,
        request: OrgRequest
    ) -> Iterator[BaseLink | LinkGroup]:
        """ Yields the edit links shown on the private view of this trait. """

        if self.editable:
            yield Link(
                _('Edit'),
                request.link(Editor('edit', self)),
                classes=('edit-link', )
            )

            assert request.path_info is not None
            yield Link(
                _('Copy'),
                request.link(Clipboard.from_url(request, request.path_info)),
                classes=('copy-link', )
            )

        if request.browser_session.has('clipboard_url'):
            css_classes = {'paste-link', 'show-new-content-placeholder'}
            attributes = {}
            clipboard = Clipboard.from_session(request)
            source = clipboard.get_object()

            # disable the paste link if the source and target traits are
            # different and display a tooltip
            if source and source.trait != self.trait:
                if source.trait == 'news':
                    title = _('A News cannot be pasted as Topic')
                else:
                    title = _('A Topic cannot be pasted as News')
                css_classes.add('disabled-link')
                attributes = {'title': title}

            yield Link(
                _('Paste'),
                request.link(Editor('paste', self.paste_target)),
                classes=css_classes,
                attributes=attributes,
            )

        if self.deletable:

            assert self.trait is not None
            trait_messages = self.trait_messages[self.trait]
            safe_delete = not self.children  # type:ignore

            if safe_delete or request.current_role == 'admin':
                extra_warning: str
                if not safe_delete:
                    extra_warning = _(
                        'Please note that this page has the following '
                        'subpages which will also be deleted:'
                    )
                else:
                    extra_warning = ''
                if isinstance(self, Page):
                    def get_all_children_titles_json(
                            page: TraitInfo) -> list[dict[str, Any]]:
                        return [
                            {
                                'title': child.title,
                                'children': get_all_children_titles_json(child)
                            }
                            for child in page.children  # type:ignore
                        ]

                    children = json.dumps(get_all_children_titles_json(self))

                items = children

                yield DeleteLink(
                    _('Delete'), request.link(self),
                    confirm=_(trait_messages['delete_question'], mapping={
                        'title': self.title
                    }),
                    yes_button_text=trait_messages['delete_button'],
                    extra_information=extra_warning,
                    redirect_after=(
                        request.link(self.parent)  # type:ignore[attr-defined]
                        if self.parent is not None  # type:ignore[attr-defined]
                        else request.class_link(Organisation)
                    ),
                    items=items,
                    scroll_hint=_('Please scroll to the bottom to enable the '
                        'confirm button.')
                )
            else:
                yield DeleteLink(
                    text=_('Delete'),
                    url=request.link(self),
                    confirm=_("This page can't be deleted."),
                    extra_information=_(
                        'This page has subpages. Only administrators can '
                        'delete pages with subpages. To delete this page, '
                        'delete all subpages first or ask an administrator '
                        'to do it for you.'
                    )
                )

        if request.is_admin and self.url_changeable:
            yield Link(
                _('Change URL'),
                request.link(Editor('change-url', self)),
                classes=('internal-url',)
            )

        if self.trait is not None:
            if (
                self.trait == 'news' and not getattr(self, 'parent', None)
            ) or self.trait != 'news':
                yield IFrameLink(
                    text=_('iFrame'),
                    url=request.link(self),
                    attrs={'class': 'new-iframe'}
                )
