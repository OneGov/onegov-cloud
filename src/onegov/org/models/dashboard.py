from attr import attrs
from itertools import groupby


from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.org.request import OrgRequest


class Dashboard:

    def __init__(self, request: 'OrgRequest') -> None:
        self.request = request

    @property
    def is_available(self) -> bool:
        """ Returns true if there are boardlets to show. """

        return self.request.app.config.boardlets_registry and True or False

    def boardlets(self) -> list[tuple['Boardlet', ...]]:
        """ Returns the boardlets, grouped/ordered by their order tuple. """

        instances = []

        for name, data in self.request.app.config.boardlets_registry.items():
            instances.append(data['cls'](
                name=name,
                order=data['order'],
                request=self.request
            ))

        instances.sort(key=lambda i: i.order)
        boardlets = []

        for group, items in groupby(instances, key=lambda i: i.order[0]):
            boardlets.append(tuple(items))

        return boardlets


class Boardlet:
    """ Base class used by all boardlets.

    Use as follows::

        from onegov.app import App

        @App.boardlet(name='foo', order=(1, 1))
        class MyBoardlet(Boardlet):
            pass

    """

    def __init__(
        self,
        name: str,
        order: tuple[int, int],
        request: 'OrgRequest'
    ) -> None:
        self.name = name
        self.order = order
        self.request = request

    @property
    def title(self) -> str:
        """ Returns the title of the boardlet, which is meant to be something
        meaningful, like the most important metric used in the boardlet.

        """
        raise NotImplementedError()

    @property
    def facts(self) -> 'Iterator[BoardletFact]':
        """ Yields facts. (:class:`BoardletFact` instances)"""

        raise NotImplementedError()

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        """ Yields one of three states:

        * 'success'
        * 'warning'
        * 'failure'

        """
        return 'success'


@attrs(auto_attribs=True)
class BoardletFact:
    """ A single boardlet fact. """

    # the text of the fact (includes the metric)
    text: str

    number: str | None = None

    icon: str | None = None

    css_class: str | None = None
