""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import JSON
from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.core.upgrade import UpgradeContext
from sqlalchemy import text
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text


@upgrade_task('Create archived results')
def create_archived_results(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Add ID to archived results')
def add_id_to_archived_results(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Update vote progress')
def update_vote_progress(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Add elected candidates to archived results')
def add_elected_candidates(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Add content columns to archived results')
def add_content_columns_to_archived_results(context: UpgradeContext) -> None:
    if not context.has_column('archived_results', 'content'):
        context.operations.add_column(
            'archived_results', Column('content', JSON)
        )


@upgrade_task('Change last change columns')
def change_last_change_columns(context: UpgradeContext) -> None:
    if not context.has_column('archived_results', 'last_modified'):
        context.operations.add_column(
            'archived_results',
            Column('last_modified', UTCDateTime, nullable=True)
        )
    if context.has_column('archived_results', 'last_result_change'):
        context.operations.execute(text(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'archived_results', 'last_result_change'
            )
        ))

    if (
        context.has_column('notifications', 'last_change')
        and not context.has_column('notifications', 'last_modified')
    ):
        context.operations.execute(text(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'notifications', 'last_change', 'last_modified'
            )
        ))

    if context.has_column('notifications', 'last_modified'):
        context.operations.execute(text(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'notifications', 'last_modified'
            )
        ))


@upgrade_task('Make subscriber polymorphic')
def make_subscriber_polymorphic(context: UpgradeContext) -> None:
    if not context.has_column('subscribers', 'type'):
        context.operations.add_column(
            'subscribers',
            Column('type', Text, nullable=True)
        )

    if (
        context.has_column('subscribers', 'phone_number')
        and not context.has_column('subscribers', 'address')
    ):
        context.operations.execute(text(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'subscribers', 'phone_number', 'address'
            )
        ))


@upgrade_task('Make notifications polymorphic')
def make_notifications_polymorphic(context: UpgradeContext) -> None:
    if (
        context.has_column('notifications', 'action')
        and not context.has_column('notifications', 'type')
    ):
        context.operations.execute(text(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'notifications', 'action', 'type'
            )
        ))
        context.operations.execute(text(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'notifications', 'type'
            )
        ))


@upgrade_task('Apply static data')
def apply_static_data(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Add election compound to archive')
def add_election_compound_to_archive(context: UpgradeContext) -> None:
    old_type = Enum('election', 'vote', name='type_of_result')
    new_type = Enum(
        'election', 'election_compound', 'vote', name='type_of_result'
    )
    tmp_type = Enum(
        'election', 'election_compound', 'vote', name='_type_of_result'
    )

    tmp_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(text(
        'ALTER TABLE archived_results ALTER COLUMN type '
        'TYPE _type_of_result USING type::text::_type_of_result'
    ))

    old_type.drop(context.operations.get_bind(), checkfirst=False)

    new_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(text(
        'ALTER TABLE archived_results ALTER COLUMN type '
        'TYPE type_of_result USING type::text::type_of_result'
    ))

    tmp_type.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Add contraints to notifications and sources')
def add_contraints_to_notifications_and_sources(
    context: UpgradeContext
) -> None:
    # We use SQL (rather than operations.xxx) so that we can drop and add
    # the constraints in one statement
    for ref in ('election', 'vote'):
        for table in ('notifications', 'upload_data_source_item'):
            context.operations.execute(text(
                f'ALTER TABLE {table} '
                f'DROP CONSTRAINT {table}_{ref}_id_fkey, '
                f'ADD CONSTRAINT {table}_{ref}_id_fkey'
                f' FOREIGN KEY ({ref}_id) REFERENCES {ref}s (id)'
                f' ON UPDATE CASCADE'
            ))


@upgrade_task('Enable expats on votes and elections')
def enable_expats(context: UpgradeContext) -> None:
    pass  # obsolete data migration


@upgrade_task('Adds active column to subscriber')
def add_active_column_to_subscriver(context: UpgradeContext) -> None:
    if not context.has_column('subscribers', 'active'):
        context.operations.add_column(
            'subscribers',
            Column('active', Boolean, nullable=True)
        )


@upgrade_task('Add election compound notification')
def add_election_compound_notification(context: UpgradeContext) -> None:
    if not context.has_column('notifications', 'election_compound_id'):
        context.operations.add_column(
            'notifications',
            Column(
                'election_compound_id',
                Text,
                ForeignKey('election_compounds.id', onupdate='CASCADE'),
                nullable=True
            )
        )


@upgrade_task('Make election day models polymorphic type non-nullable')
def make_election_day_models_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    for table in ('notifications', 'subscribers'):
        if context.has_table(table):
            context.operations.execute(text(f"""
                UPDATE {table} SET type = 'generic' WHERE type IS NULL;
            """))

            context.operations.alter_column(table, 'type', nullable=False)


@upgrade_task('Add domain and segment to screens')
def add_domain_and_segment_to_screens(context: UpgradeContext) -> None:
    for column in ('domain', 'domain_segment'):
        if not context.has_column('election_day_screens', column):
            context.operations.add_column(
                'election_day_screens',
                Column(column, Text, nullable=True)
            )


@upgrade_task('Add has results to archived results')
def add_has_results_to_archived_results(context: UpgradeContext) -> None:
    if not context.has_column('archived_results', 'has_results'):
        context.operations.add_column(
            'archived_results',
            Column('has_results', Boolean, nullable=True)
        )


@upgrade_task('Delete websocket notifications')
def delete_websocket_notifications(context: UpgradeContext) -> None:
    context.operations.execute(text("""
        DELETE FROM notifications WHERE type = 'websocket';
    """))


@upgrade_task('Make upload token none-nullable')
def make_upload_take_none_nullable(context: UpgradeContext) -> None:
    if context.has_column('upload_tokens', 'token'):
        context.operations.alter_column(
            'upload_tokens', 'token', nullable=False
        )


@upgrade_task('Add domain and segment to subscribers')
def add_domain_and_segment_to_subscribers(context: UpgradeContext) -> None:
    for column in ('domain', 'domain_segment'):
        if not context.has_column('subscribers', column):
            context.operations.add_column(
                'subscribers',
                Column(column, Text, nullable=True)
            )


@upgrade_task('Add short title')
def add_short_title(context: UpgradeContext) -> None:
    tables = ('elections', 'election_compounds', 'votes')
    for table in tables:
        if not context.has_column(table, 'short_title_translations'):
            context.operations.add_column(
                table,
                Column('short_title_translations', HSTORE, nullable=True)
            )


@upgrade_task('Add active/inactive since columns to subscribers')
def add_active_inactive_since_columns(context: UpgradeContext) -> None:
    if not context.has_column('subscribers', 'active_since'):
        assert not context.has_column('subscribers', 'inactive_since')
        context.operations.add_column(
            'subscribers', Column('active_since', UTCDateTime, default=None)
        )
        context.operations.add_column(
            'subscribers', Column('inactive_since', UTCDateTime, default=None)
        )
        # pre-fill the dates where we can make an educated guess
        context.operations.execute(text("""
            UPDATE subscribers SET inactive_since = modified
             WHERE modified >= TIMESTAMP '2022-02-07'
               AND active IS FALSE
        """))
        context.operations.execute(text("""
            UPDATE subscribers SET active_since = created
             WHERE modified IS NOT NULL
               AND type = 'sms'
        """))


@upgrade_task('Add translation columns to archived results')
def add_translation_columns_to_archived_results(
    context: UpgradeContext
) -> None:
    # for complex votes we need translations for proposal title,
    # counter proposal title and tie breaker title.
    if not context.has_column('archived_results',
                              'title_proposal_translations'):
        context.operations.add_column(
            'archived_results',
            Column(
                'title_proposal_translations', HSTORE, nullable=True)
        )
    if not context.has_column('archived_results',
                              'title_counter_proposal_translations'):
        context.operations.add_column(
            'archived_results',
            Column(
                'title_counter_proposal_translations', HSTORE, nullable=True)
        )
    if not context.has_column('archived_results',
                              'title_tie_breaker_translations'):
        context.operations.add_column(
            'archived_results',
            Column(
                'title_tie_breaker_translations', HSTORE, nullable=True)
        )
