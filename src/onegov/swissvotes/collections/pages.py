from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.core.orm.abstract import MoveDirection
from onegov.swissvotes.app import get_i18n_used_locales
from onegov.swissvotes.models import TranslatablePage


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Query


class TranslatablePageCollection(GenericCollection[TranslatablePage]):

    """ A collection of translatable content pages. """

    @property
    def model_class(self) -> type[TranslatablePage]:
        return TranslatablePage

    def setdefault(self, id: str) -> TranslatablePage:
        locales = get_i18n_used_locales()
        return self.by_id(id) or self.add(
            id=id,
            title_translations={locale: id for locale in locales},
            content_translations={locale: id for locale in locales},
            order=-1
        )

    def query(self) -> Query[TranslatablePage]:
        return super().query().order_by(TranslatablePage.order)

    def add(self, **kwargs: Any) -> TranslatablePage:
        """ Adds a new page. """

        page = super().add(**kwargs)
        for order, sibling in enumerate(page.siblings):
            sibling.order = order
        return page

    def move(
        self,
        subject: TranslatablePage,
        target: TranslatablePage,
        direction: MoveDirection
    ) -> None:
        """ Takes the given subject and moves it somehwere in relation to the
        target.

        :subject:
            The page to be moved.

        :target:
            The page above which or below which the subject is moved.

        :direction:
            The direction relative to the target. Either
            :attr:`MoveDirection.above` if the subject should be moved
            above the target, or :attr:`MoveDirection.below` if the subject
            should be moved below the target.

        """
        assert direction in MoveDirection
        assert subject != target

        siblings = target.siblings.all()

        def new_order() -> Iterator[TranslatablePage]:
            for sibling in siblings:
                if sibling == subject:
                    continue

                if sibling != target:
                    yield sibling

                elif direction == MoveDirection.above:
                    yield subject
                    yield target

                elif direction == MoveDirection.below:
                    yield target
                    yield subject

        for order, sibling in enumerate(new_order()):
            sibling.order = order
