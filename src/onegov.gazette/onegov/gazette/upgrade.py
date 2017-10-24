""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.gazette.collections.categories import CategoryCollection


@upgrade_task('Migrate gazette categories', always_run=True)
def migrate_categories(context):
    principal = getattr(context.app, 'principal', None)
    if not principal:
        return False

    categories = getattr(principal, '_categories', None)
    if not categories:
        return False

    if not context.has_table('gazette_categories'):
        return False

    session = context.app.session_manager.session()
    count = session.execute("select count(*) from gazette_categories")
    if count.scalar() != 0:
        return False

    collection = CategoryCollection(session)
    for name, title in categories.items():
        collection.add_root(name=name, title=title, active=True)
