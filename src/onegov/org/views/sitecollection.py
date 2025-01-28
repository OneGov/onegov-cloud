from __future__ import annotations

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.models import SiteCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.org.request import OrgRequest


@OrgApp.json(model=SiteCollection, permission=Private)
def get_site_collection(
    self: SiteCollection,
    request: OrgRequest
) -> JSON_ro:
    """ Returns a list of internal links to be used by the redactor.

    See `<https://imperavi.com/redactor/plugins/predefined-links/>`_

    """

    objects = self.get()

    groups = [
        ('topics', request.translate(_('Topics'))),
        ('news', request.translate(_('Latest news'))),
        ('imagesets', request.translate(_('Photo Albums'))),
        ('forms', request.translate(_('Forms'))),
        ('directories', request.translate(_('Directories'))),
        ('resources', request.translate(_('Resources'))),
    ]

    # in addition to the default url/name pairings we use a group
    # label which will be used as optgroup label
    return [
        {
            'group': label,
            'name': obj.title,
            'url': request.link(obj)
        }
        for id, label in groups
        for obj in objects[id]
    ]
