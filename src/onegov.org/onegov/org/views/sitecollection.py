from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.models import SiteCollection


@OrgApp.json(model=SiteCollection, permission=Private)
def get_site_collection(self, request):
    """ Returns a list of internal links to be used by the redactor.

    See `<http://imperavi.com/redactor/plugins/predefined-links/>`_

    """

    objects = self.get()

    groups = [
        ('topics', request.translate(_("Topics"))),
        ('news', request.translate(_("Latest news"))),
        ('imagesets', request.translate(_("Photo Albums"))),
        ('forms', request.translate(_("Forms"))),
        ('directories', request.translate(_("Directories"))),
        ('resources', request.translate(_("Resources"))),
    ]

    links = []

    for id, label in groups:
        for obj in objects[id]:
            # in addition to the default url/name pairings we use a group
            # label which will be used as optgroup label
            links.append({
                'group': label,
                'name': obj.title,
                'url': request.link(obj)
            })

    return links
