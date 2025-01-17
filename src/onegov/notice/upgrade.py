""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add categories column to official notices')
def add_categories(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'categories'):
        context.operations.add_column(
            'official_notices',
            Column('categories', HSTORE, nullable=True)
        )


@upgrade_task('Add organizations column to official notices')
def add_organizations(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'organizations'):
        context.operations.add_column(
            'official_notices',
            Column('organizations', HSTORE, nullable=True)
        )


@upgrade_task('Add author fields to official notices')
def add_author_fields(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'author_name'):
        context.operations.add_column(
            'official_notices',
            Column('author_name', Text, nullable=True)
        )
    if not context.has_column('official_notices', 'author_place'):
        context.operations.add_column(
            'official_notices',
            Column('author_place', Text, nullable=True)
        )
    if not context.has_column('official_notices', 'author_date'):
        context.operations.add_column(
            'official_notices',
            Column('author_date', UTCDateTime, nullable=True)
        )


@upgrade_task('Add an imported state to official notices')
def add_imported_state_to_notices(context: UpgradeContext) -> None:
    old = ['drafted', 'submitted', 'published', 'rejected', 'accepted']
    new = [*old, 'imported']
    old_type = Enum(*old, name='official_notice_state')
    new_type = Enum(*new, name='official_notice_state')
    tmp_type = Enum(*new, name='_official_notice_state')

    tmp_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(
        'ALTER TABLE official_notices ALTER COLUMN state '
        'TYPE _official_notice_state USING state::text::_official_notice_state'
    )
    old_type.drop(context.operations.get_bind(), checkfirst=False)
    new_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(
        'ALTER TABLE official_notices ALTER COLUMN state '
        'TYPE official_notice_state USING state::text::official_notice_state'
    )
    tmp_type.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Add a souurce column to official notices')
def add_source_column_to_notices(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'source'):
        context.operations.add_column(
            'official_notices',
            Column('source', Text, nullable=True)
        )


@upgrade_task('Add an expiry date column to official notices')
def add_expiry_date_column_to_notices(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'expiry_date'):
        context.operations.add_column(
            'official_notices',
            Column('expiry_date', UTCDateTime, nullable=True)
        )


@upgrade_task('Add note column to official notices')
def add_note_to_notices(context: UpgradeContext) -> None:
    if not context.has_column('official_notices', 'note'):
        context.operations.add_column(
            'official_notices',
            Column('note', Text, nullable=True)
        )


@upgrade_task('Make official notice polymorphic type non-nullable')
def make_official_notice_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    if context.has_table('official_notices'):
        context.operations.execute("""
            UPDATE official_notices SET type = 'generic' WHERE type IS NULL;
        """)

        context.operations.alter_column('official_notices', 'type',
                                        nullable=False)
