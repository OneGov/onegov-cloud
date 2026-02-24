""" Contains the model describing the page editor. """
from __future__ import annotations


from typing import overload, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypeAlias, TypeGuard

    from .traitinfo import TraitInfo

    PageActionWithoutPage: TypeAlias = Literal['new', 'new-root']
    PageActionWithPage: TypeAlias = Literal[
        'edit', 'delete', 'paste', 'change-url', 'sort', 'move'
    ]
    PageAction: TypeAlias = PageActionWithoutPage | PageActionWithPage


class Editor:
    """ Defines the model for the page editor. Required because pages need
    to be edited outside their url structure, since their urls are absorbed
    completely and turned into SQL queries.

    """
    @overload
    def __init__(
        self,
        action: PageActionWithoutPage,
        page: None,
        trait: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        action: PageAction,
        page: TraitInfo,
        trait: str | None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        action: Literal['new', 'new-root'],
        page: None,
        trait: str | None = None
    ) -> None: ...

    def __init__(
        self,
        action: PageAction,
        # NOTE: We would like this to be (Page & TraitInfo) | None
        page: TraitInfo | None,
        trait: str | None = None
    ) -> None:
        """ The editor is defined by an action and a page/context.

        :action:
            One of 'new', 'edit' or 'delete'.

        :page:
            The 'context' of the action. The actual page in the case of 'edit'
            and 'delete'. The parent in the case of 'new' or 'paste'.

            New pages inherit the type from the parent.

        :trait:
            The trait of the page. Currently, either 'link' or 'page'.
            Only necessary if it's a new page. The trait controls the content
            of the page and leads to different forms.

            See :mod:`onegov.org.models.page`.

        """

        assert self.is_supported_action(action)

        self.action = action
        self.page = page
        if action not in ('new', 'new-root') or not trait:
            assert page is not None
            trait = page.trait

        assert trait is not None
        self.trait = trait

    @staticmethod
    def is_supported_action(action: str) -> TypeGuard[PageAction]:
        """ Returns True if the given action is supported. """
        return action in {
            'new', 'new-root', 'paste', 'edit', 'delete', 'change-url',
            'sort', 'move'
        }

    @property
    def page_id(self) -> int:
        """ Returns the page id so morepath can create a link to this. """
        if self.action == 'new-root':
            return 0
        assert self.page is not None and hasattr(self.page, 'id')
        return self.page.id
