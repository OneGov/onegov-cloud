""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Vote
from onegov.core.orm.types import HSTORE, JSON
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column, Enum, Integer, Text
from sqlalchemy.engine.reflection import Inspector


@upgrade_task('Rename yays to yeas', always_run=True)
def rename_yays_to_yeas(context):

    if context.has_column('ballot_results', 'yeas'):
        return False
    else:
        context.operations.alter_column(
            'ballot_results', 'yays', new_column_name='yeas')


@upgrade_task('Add shortcode column')
def add_shortcode_column(context):
    context.operations.add_column('votes', Column('shortcode', Text()))


@upgrade_task('Enable translation of vote title')
def enable_translation_of_vote_title(context):

    # get the existing votes before removing the old column
    query = context.session.execute('SELECT id, title FROM votes')
    votes = dict(query.fetchall())

    context.operations.drop_column('votes', 'title')
    context.operations.add_column('votes', Column(
        'title_translations', HSTORE, nullable=True
    ))

    for vote in context.session.query(Vote).all():
        vote.title_translations = {
            locale: votes[vote.id].strip()
            for locale in context.app.locales
        }
    context.session.flush()

    context.operations.alter_column(
        'votes', 'title_translations', nullable=False
    )


@upgrade_task('Add absolute majority column')
def add_absolute_majority_column(context):
    if not context.has_column('elections', 'absolute_majority'):
        context.operations.add_column(
            'elections',
            Column('absolute_majority', Integer())
        )


@upgrade_task('Add meta data')
def add_meta_data_columns(context):
    if not context.has_column('elections', 'meta'):
        context.operations.add_column('elections', Column('meta', JSON()))

    if not context.has_column('votes', 'meta'):
        context.operations.add_column('votes', Column('meta', JSON()))


@upgrade_task('Add municipality domain of influence')
def add_municipality_domain(context):
    # Rename the columns
    renames = (
        ('elections', 'total_municipalities', 'total_entities'),
        ('elections', 'counted_municipalities', 'counted_entities'),
        ('election_results', 'municipality_id', 'entity_id'),
        ('ballot_results', 'municipality_id', 'entity_id'),
    )

    for table, old, new in renames:
        if context.has_column(table, old):
            context.operations.alter_column(table, old, new_column_name=new)

    # Add the new domain, see http://stackoverflow.com/a/14845740
    table_names = []
    inspector = Inspector(context.operations_connection)
    if 'elections' in inspector.get_table_names(context.schema):
        table_names.append('elections')
    if 'votes' in inspector.get_table_names(context.schema):
        table_names.append('votes')
    if 'archived_results' in inspector.get_table_names(context.schema):
        table_names.append('archived_results')

    old_type = Enum('federation', 'canton', name='domain_of_influence')
    new_type = Enum('federation', 'canton', 'municipality',
                    name='domain_of_influence')
    tmp_type = Enum('federation', 'canton', 'municipality',
                    name='_domain_of_influence')

    tmp_type.create(context.operations.get_bind(), checkfirst=False)

    for table_name in table_names:
        context.operations.execute(
            (
                'ALTER TABLE {} ALTER COLUMN domain TYPE _domain_of_influence '
                'USING domain::text::_domain_of_influence'
            ).format(table_name)
        )

    old_type.drop(context.operations.get_bind(), checkfirst=False)

    new_type.create(context.operations.get_bind(), checkfirst=False)

    for table_name in table_names:
        context.operations.execute(
            (
                'ALTER TABLE {} ALTER COLUMN domain TYPE domain_of_influence '
                'USING domain::text::domain_of_influence'
            ).format(table_name)
        )

    tmp_type.drop(context.operations.get_bind(), checkfirst=False)
