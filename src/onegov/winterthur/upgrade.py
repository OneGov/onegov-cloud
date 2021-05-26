""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from onegov.org.models import Organisation
from sqlalchemy import Column, Integer, Enum

from onegov.winterthur.models.mission_report import MISSION_TYPES


@upgrade_task('Change the default geo provider')
def change_default_geo_provider(context):

    org = context.session.query(Organisation).first()

    if org is None:
        return False

    if "Strassenverzeichnis" not in org.meta['homepage_structure']:
        return False

    org.meta['geo_provider'] = 'geo-vermessungsamt-winterthur'


@upgrade_task('Adds mission count and type to reports')
def add_mission_count_and_type_to_reports(context):
    if not context.has_column('mission_reports', 'mission_type'):
        context.add_column_with_defaults(
            'mission_reports',
            Column(
                'mission_type',
                Enum(*MISSION_TYPES, name='mission_type'),
                default='single'),
            default=lambda x: 'single'
        )

    if not context.has_column('mission_reports', 'mission_count'):
        context.add_column_with_defaults(
            'mission_reports',
            Column('mission_count', Integer, default=1),
            default=lambda x: 1
        )
