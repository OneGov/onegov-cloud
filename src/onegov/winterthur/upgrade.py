""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.org.models import Organisation
from onegov.winterthur.models.mission_report import MISSION_TYPES
from sqlalchemy import Column, Integer, Enum


@upgrade_task('Change the default geo provider')
def change_default_geo_provider(context: UpgradeContext) -> bool | None:

    org = context.session.query(Organisation).first()

    if org is None:
        return False

    if 'Strassenverzeichnis' not in org.meta['homepage_structure']:
        return False

    org.meta['geo_provider'] = 'geo-vermessungsamt-winterthur'
    return None


@upgrade_task('Adds mission count and type to reports')
def add_mission_count_and_type_to_reports(context: UpgradeContext) -> None:
    if not context.has_column('mission_reports', 'mission_type'):
        context.add_column_with_defaults(
            'mission_reports',
            Column(
                'mission_type',
                Enum(*MISSION_TYPES, name='mission_type'),
                default='single'),
            default=lambda x: 'single'  # type: ignore
        )

    if not context.has_column('mission_reports', 'mission_count'):
        context.add_column_with_defaults(
            'mission_reports',
            Column('mission_count', Integer, default=1),
            default=lambda x: 1
        )


@upgrade_task('Add timestamps to street')
def add_timestamps_to_street(context: UpgradeContext) -> None:
    if not context.has_column('winterthur_addresses', 'created'):
        context.operations.add_column('winterthur_addresses', Column(
            'created', UTCDateTime
        ))
    if not context.has_column('winterthur_addresses', 'modified'):
        context.operations.add_column('winterthur_addresses', Column(
            'modified', UTCDateTime
        ))
