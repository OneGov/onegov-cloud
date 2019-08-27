""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.org.models import Organisation


@upgrade_task("Add default values for page breaks of PDFs")
def add_default_value_for_pagebreak_pdf(context):

    """ Adds the elected candidates to the archived results,

    """
    session = context.session
    if context.has_column('organisations', 'meta'):
        for org in session.query(Organisation).all():
            org.meta['page_break_on_level_root_pdf'] = 1
            org.meta['page_break_on_level_orga_pdf'] = 1
