""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from onegov.town import initial_content


@upgrade_task(name="Add root organizations")
def add_root_organizations(context):
    initial_content.add_root_organizations(context.session)
