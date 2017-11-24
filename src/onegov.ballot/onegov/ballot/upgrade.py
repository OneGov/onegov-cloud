""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Vote
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import Text
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


@upgrade_task('Add status')
def add_status_columns(context):
    if not context.has_column('elections', 'status'):
        context.operations.add_column(
            'elections',
            Column(
                'status',
                Enum(
                    'unknown',
                    'interim',
                    'final',
                    name='election_or_vote_status'
                ),
                nullable=True
            )
        )

    if not context.has_column('votes', 'status'):
        context.operations.add_column(
            'votes',
            Column(
                'status',
                Enum(
                    'unknown',
                    'interim',
                    'final',
                    name='election_or_vote_status'
                ),
                nullable=True
            )
        )


@upgrade_task('Add status')
def add_status_columns(context):
    if not context.has_column('elections', 'status'):
        context.operations.add_column(
            'elections',
            Column(
                'status',
                Enum(
                    'unknown',
                    'interim',
                    'final',
                    name='election_or_vote_status'
                ),
                nullable=True
            )
        )

    if not context.has_column('votes', 'status'):
        context.operations.add_column(
            'votes',
            Column(
                'status',
                Enum(
                    'unknown',
                    'interim',
                    'final',
                    name='election_or_vote_status'
                ),
                nullable=True
            )
        )


@upgrade_task('Add party to candidate')
def add_candidate_party_column(context):
    for table in ['candidates', 'candiates']:
        if context.has_table(table):
            if not context.has_column(table, 'party'):
                context.operations.add_column(
                    table,
                    Column('party', Text, nullable=True)
                )


@upgrade_task('Rename candidates tables')
def rename_candidates_tables(context):
    for old_name, new_name in (
        ('candiate_results', 'candidate_results'),
        ('candiates', 'candidates'),
    ):
        if context.has_table(old_name):
            if context.has_table(new_name):
                context.operations.drop_table(new_name)
            context.operations.rename_table(old_name, new_name)


@upgrade_task('Adds ballot title')
def add_ballot_title(context):
    context.operations.add_column('ballots', Column(
        'title_translations', HSTORE, nullable=True
    ))


@upgrade_task('Add content columns')
def add_content_columns(context):
    if not context.has_column('elections', 'content'):
        context.operations.add_column('elections', Column('content', JSON))

    if not context.has_column('votes', 'content'):
        context.operations.add_column('votes', Column('content', JSON))


@upgrade_task('Add vote type column')
def add_vote_type_column(context):
    if not context.has_column('votes', 'type'):
        context.operations.add_column('votes', Column('type', Text))

        for vote in context.session.query(Vote).all():
            meta = vote.meta or {}
            vote.type = meta.get('vote_type', 'simple')
            if 'vote_type' in meta:
                del vote.meta['vote_type']
