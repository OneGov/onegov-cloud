""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from markupsafe import Markup
from onegov.core.upgrade import upgrade_task
from onegov.core.upgrade import UpgradeContext
from onegov.core.utils import linkify
from onegov.org.models import Organisation
from onegov.people import Agency


@upgrade_task('Add default values for page breaks of PDFs')
def add_default_value_for_pagebreak_pdf(context: UpgradeContext) -> None:

    """ Adds the elected candidates to the archived results,

    """
    session = context.session
    if context.has_column('organisations', 'meta'):
        for org in session.query(Organisation).all():
            org.meta['page_break_on_level_root_pdf'] = 1
            org.meta['page_break_on_level_org_pdf'] = 1


@upgrade_task('Convert Agency.portrait to a html')
def convert_agency_portrait_to_html(context: UpgradeContext) -> None:
    session = context.session
    if context.has_column('agencies', 'portrait'):
        for agency in session.query(Agency).all():
            agency.portrait = Markup('<p>{}</p>').format(
                linkify(agency.portrait).replace('\n', Markup('<br>')))


@upgrade_task('Replace person.address in Agency.export_fields')
def replace_removed_export_fields(context: UpgradeContext) -> None:
    session = context.session
    if context.has_column('agencies', 'meta'):
        for agency in session.query(Agency).all():
            export_fields = agency.meta.get('export_fields', [])
            if 'person.address' in export_fields:
                # replace old shared field with new split field
                # but preserving the order
                idx = export_fields.index('person.address')
                export_fields = [
                    *export_fields[:idx],
                    'person.location_address',
                    'person.location_code_city',
                    'person.postal_address',
                    'person.postal_code_city',
                    *export_fields[idx + 1:]
                ]
                agency.meta['export_fields'] = export_fields
