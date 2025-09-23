from __future__ import annotations


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
