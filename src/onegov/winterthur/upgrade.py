""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from onegov.org.models import Organisation


@upgrade_task('Change the default geo provider', always_run=True)
def change_default_geo_provider(context):

    org = context.session.query(Organisation).first()

    if org is None:
        return False

    if "Strassenverzeichnis" not in org.meta['homepage_structure']:
        return False

    org.meta['geo_provider'] = 'geo-vermessungsamt-winterthur'
