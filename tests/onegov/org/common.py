from __future__ import annotations

from onegov.ticket import Handler, Ticket


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core import Framework
    from onegov.core.cronjobs import Job
    from onegov.ticket.handler import HandlerRegistry


def get_cronjob_by_name(app: Framework, name: str) -> Job[Any] | None:
    for cronjob in app.config.cronjob_registry.cronjobs.values():
        if name in cronjob.name:
            return cronjob
    return None


def get_cronjob_url(cronjob: Job[Any]) -> str:
    return f'/cronjobs/{cronjob.id}'


def edit_bar_links(page: Any, attrib: str | None = None) -> list[Any]:
    links = page.pyquery('.edit-bar a')
    if attrib:
        if attrib == 'text':
            return [li.text for li in links]
        return [li.attrib[attrib] for li in links]
    return links


class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EHO'}  # type: ignore[dict-item]


class EchoHandler(Handler):
    handler_title = "Echo"

    @property
    def deleted(self) -> bool:
        return False

    @property
    def email(self) -> str | None:
        return self.data.get('email')

    @property
    def title(self) -> Any:
        return self.data.get('title')

    @property
    def subtitle(self) -> str | None:
        return self.data.get('subtitle')

    @property
    def group(self) -> str | None:
        return self.data.get('group')

    def get_summary(self, request: object) -> Any:
        return self.data.get('summary')

    def get_links(self, request: object) -> Any:
        return self.data.get('links')


def register_echo_handler(handlers: HandlerRegistry) -> None:
    handlers.register('EHO', EchoHandler)
