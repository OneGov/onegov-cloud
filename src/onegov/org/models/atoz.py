from __future__ import annotations

from collections import OrderedDict
from itertools import groupby
from unidecode import unidecode


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.org.request import OrgRequest


class AtoZ[T]:

    def __init__(self, request: OrgRequest) -> None:
        self.request = request

    def sortkey(self, item: T) -> str:
        return unidecode(self.get_title(item)[0].upper())

    def get_items_by_letter(self) -> dict[str, tuple[T, ...]]:
        items_by_letter = OrderedDict()

        for letter, items in groupby(self.get_items(), self.sortkey):
            items_by_letter[unidecode(letter)] = tuple(
                sorted(items, key=lambda i: unidecode(self.get_title(i)))
            )

        return items_by_letter

    def get_title(self, item: T) -> str:
        raise NotImplementedError

    def get_items(self) -> Sequence[T]:
        raise NotImplementedError
