from __future__ import annotations

from onegov.ticket import Handler, Ticket


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core import Framework
    from onegov.core.cronjobs import Job


def get_cronjob_by_name(app: Framework, name: str) -> Job[Any] | None:
    for cronjob in app.config.cronjob_registry.cronjobs.values():
        if name in cronjob.name:
            return cronjob


def get_cronjob_url(cronjob: Job[Any]) -> str:
    return '/cronjobs/{}'.format(cronjob.id)


def edit_bar_links(page: Any, attrib: str | None = None) -> list[Any]:
    links = page.pyquery('.edit-bar a')
    if attrib:
        if attrib == 'text':
            return [li.text for li in links]
        return [li.attrib[attrib] for li in links]
    return links


class EchoTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EHO'}


class EchoHandler(Handler):
    handler_title = "Echo"

    @property
    def deleted(self):
        return False

    @property
    def email(self):
        return self.data.get('email')

    @property
    def title(self):
        return self.data.get('title')

    @property
    def subtitle(self):
        return self.data.get('subtitle')

    @property
    def group(self):
        return self.data.get('group')

    def get_summary(self, request):
        return self.data.get('summary')

    def get_links(self, request):
        return self.data.get('links')

    @property
    def ticket_deletable(self):
        return self.ticket.state == 'archived'

    def prepare_delete_ticket(self):
        assert self.ticket_deletable
        pass


def register_echo_handler(handlers):
    handlers.register('EHO', EchoHandler)
