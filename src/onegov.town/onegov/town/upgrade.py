""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.abstract import sort_siblings
from onegov.core.upgrade import upgrade_task
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.page import PageCollection
from onegov.town import TownApp
from onegov.town.initial_content import add_builtin_forms, add_resources
from onegov.town.models.extensions import ContactExtension


@upgrade_task('Update builtin forms')
def update_builtin_forms(context, always_run=True):
    add_builtin_forms(context.session)


@upgrade_task('Add initial libres resources')
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


@upgrade_task('Update contact html')
def change_contact_html(context):
    items = []

    items.extend(PageCollection(context.session).query().all())
    items.extend(FormCollection(context.session).definitions.query().all())

    if isinstance(context.app, TownApp):
        items.extend(
            ResourceCollection(context.app.libres_context).query().all()
        )

    for item in items:
        if not isinstance(item, ContactExtension):
            continue
        if not item.contact:
            continue

        # forces a re-render of the contact html
        item.contact = item.contact
