from __future__ import annotations

from attr import attrs
from itertools import groupby
from operator import attrgetter


from typing import ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.org.directives import BoardletConfig
    from onegov.org.request import OrgRequest


class Dashboard:

    kind: ClassVar[Literal['user', 'citizen']] = 'user'

    def __init__(self, request: OrgRequest) -> None:
        self.request = request

    @property
    def boardlet_configs(self) -> dict[str, BoardletConfig]:
        """ The appropriate set of `BoardletConfig` for our kind. """

        return self.request.app.config.boardlets_registry[self.kind]

    @property
    def is_available(self) -> bool:
        """ True if there are `Boardlet`s to display. """

        return self.boardlet_configs and True or False

    def boardlets(self) -> list[tuple[Boardlet, ...]]:
        """ Returns the boardlets, grouped/ordered by their order tuple. """

        instances = sorted((
            data['cls'](
                name=name,
                order=data['order'],
                icon=data['icon'],
                request=self.request
            )
            for name, data in self.boardlet_configs.items()
        ), key=attrgetter('order'))

        return [
            tuple(items)
            for _, items in groupby(instances, key=lambda i: i.order[0])
        ]


class CitizenDashboard(Dashboard):

    kind = 'citizen'


class Boardlet:
    """ Base class used by all boardlets.

    Use as follows::

        from onegov.app import App

        @App.boardlet(name='foo', order=(1, 1), icon='')
        class MyBoardlet(Boardlet):
            pass

    """

    def __init__(
        self,
        name: str,
        order: tuple[int, int],
        icon: str,
        request: OrgRequest
    ) -> None:
        self.name = name
        self.order = order
        self.icon = icon or ''
        self.request = request

    @property
    def title(self) -> str:
        """The title of the boardlet — typically the most important metric."""
        raise NotImplementedError()

    @property
    def url(self) -> str | None:
        """ A URL the title of the boardlet should link to. """
        return None

    @property
    def facts(self) -> Iterator[BoardletFact]:
        """ Facts as :class:`BoardletFact` instances. """

        raise NotImplementedError()

    @property
    def is_available(self) -> bool:
        """ True if the boardlet is active/has data. """
        return True

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        """ One of three states:

        * 'success'
        * 'warning'
        * 'failure'

        """
        return 'success'


@attrs(auto_attribs=True)
class BoardletFact:
    """ A single boardlet fact. """

    # the text of the fact (not including the metric)
    text: str

    # the metric of the fact
    number: int | float | str | None = None

    # link to be displayed as tuple of link, link text
    link: tuple[str, str] | None = None

    # the font awesome (fa-*) icon to use, if any
    icon: str | None = None

    # visibility icon right behind text/link
    visibility_icon: str | None = None

    # title of the icon (hover text)
    icon_title: str | None = None

    css_class: str | None = None
