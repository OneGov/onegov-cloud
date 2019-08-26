""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from onegov.org.models import Organisation


@upgrade_task('Add PDF Page Break Settings')
def update_pdf_page_break_settings(context):
    session = context.app.session()
    if context.has_column('organisations', 'meta'):
        for org in session.query(Organisation).all():
            org.meta['page_break_on_level_root_pdf'] = 1
            org.meta['page_break_on_level_orga_pdf'] = 1
