""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import linkify
from onegov.org.models import Organisation
from onegov.people import Agency
from sqlalchemy import Column
from sqlalchemy import Text


@upgrade_task("Add default values for page breaks of PDFs")
def add_default_value_for_pagebreak_pdf(context):

    """ Adds the elected candidates to the archived results,

    """
    session = context.session
    if context.has_column('organisations', 'meta'):
        for org in session.query(Organisation).all():
            org.meta['page_break_on_level_root_pdf'] = 1
            org.meta['page_break_on_level_org_pdf'] = 1


@upgrade_task("Convert Agency.portrait to a html")
def convert_agency_portrait_to_html(context):
    session = context.session
    if context.has_column('agencies', 'portrait'):
        for agency in session.query(Agency).all():
            agency.portrait = '<p>{}</p>'.format(
                linkify(agency.portrait).replace('\n', '<br>'))


@upgrade_task('Add address columns to agency')
def add_address_columns_to_agency(context):
    if not context.has_column('agencies', 'street'):
        context.operations.add_column('agencies', Column(
            'street', Text, nullable=True
        ))
    if not context.has_column('agencies', 'zip_code'):
        context.operations.add_column('agencies', Column(
            'zip_code', Text, nullable=True
        ))
    if not context.has_column('agencies', 'city'):
        context.operations.add_column('agencies', Column(
            'city', Text, nullable=True
        ))
