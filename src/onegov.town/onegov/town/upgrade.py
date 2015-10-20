""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.abstract import sort_siblings
from onegov.core.upgrade import upgrade_task
from onegov.town import TownApp
from onegov.town.initial_content import add_resources
from onegov.page import PageCollection


@upgrade_task('Add initial libres resources', always_run=False)
def add_initial_libres_resources(context):
    if isinstance(context.app, TownApp):
        add_resources(context.app.libres_context)


@upgrade_task('Add order to all pages')
def add_order_to_all_pages(context):
    pages = PageCollection(context.session)
    processed_siblings = set()

    for page in pages.query(ordered=False):
        siblings = page.siblings.all()

        ids = {sibling.id for sibling in siblings}
        if ids <= processed_siblings:
            continue

        sort_siblings(siblings, key=PageCollection.sort_key)

        processed_siblings.update(ids)
