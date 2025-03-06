""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations
from uuid import uuid4

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB

from onegov.core.orm.types import UUID
from onegov.core.upgrade import upgrade_task, UpgradeContext


@upgrade_task('fts: Adds search index table to each schema')
def adds_search_index_table(context: UpgradeContext) -> None:
    if not context.has_table('search_index'):
        context.operations.create_table(
            'search_index',
            Column('id', UUID, primary_key=True, default=uuid4),
            Column('owner_id_int', Integer, nullable=True),
            Column('owner_id_uuid', UUID, nullable=True),
            Column('owner_type', String, nullable=False),
            Column('fts_idx_data', JSONB, default={}),
            Column('fts_idx', TSVECTOR)
        )
