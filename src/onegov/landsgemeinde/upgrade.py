""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.upgrade import UpgradeContext
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy import Time
from onegov.landsgemeinde.collections import VotumCollection
from onegov.core.utils import relative_url


@upgrade_task('Add last modified column')
def add_last_modified_to_assemblies(context: UpgradeContext) -> None:
    if not context.has_column('landsgemeinde_assemblies', 'last_modified'):
        context.operations.add_column(
            'landsgemeinde_assemblies',
            Column('last_modified', UTCDateTime())
        )


@upgrade_task('Remove start time from agenda item and votum')
def remove_start_time_from_agenda_item_and_votum(
    context: UpgradeContext
) -> None:
    for table in ('landsgemeinde_agenda_items', 'landsgemeinde_vota'):
        if context.has_column(table, 'start'):
            context.operations.drop_column(table, 'start')


@upgrade_task('Add last modified column to agenda items')
def add_last_modified_to_agenda_items(context: UpgradeContext) -> None:
    if not context.has_column('landsgemeinde_agenda_items', 'last_modified'):
        context.operations.add_column(
            'landsgemeinde_agenda_items',
            Column('last_modified', UTCDateTime())
        )


@upgrade_task('Add person picture url column')
def add_person_picture_url_column(context: UpgradeContext) -> None:
    if not context.has_column('landsgemeinde_vota', 'person_picture'):
        context.operations.add_column(
            'landsgemeinde_vota',
            Column('person_picture', Text, nullable=True)
        )

    session = context.app.session_manager.session()
    vota = VotumCollection(session).query()
    for votum in vota:
        for file in votum.files:
            if file.name == 'person_picture':
                file.type = 'image'
                file.name = file.reference.filename
                votum.person_picture = relative_url(context.request.link(file))


@upgrade_task('Add start time to agenda item')
def add_start_time_to_agenda_item(context: UpgradeContext) -> None:
    if not context.has_column('landsgemeinde_agenda_items', 'start_time'):
        context.operations.add_column(
            'landsgemeinde_agenda_items',
            Column('start_time', Time, nullable=True)
        )


@upgrade_task('Add start time to assembly')
def add_start_time_to_assembly(context: UpgradeContext) -> None:
    if not context.has_column('landsgemeinde_assemblies', 'start_time'):
        context.operations.add_column(
            'landsgemeinde_assemblies',
            Column('start_time', Time, nullable=True)
        )
