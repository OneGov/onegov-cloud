""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import JSON
from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task, UpgradeContext
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.engine.reflection import Inspector


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence


def alter_domain_of_influence(
    context: UpgradeContext,
    old: 'Sequence[str]',
    new: 'Sequence[str]'
) -> None:
    # see http://stackoverflow.com/a/14845740

    # Todo: Check if old exists
    old_type = Enum(*old, name='domain_of_influence')

    # Change current types to a temporary one
    tmp_type = Enum(*new, name='_domain_of_influence')
    tmp_type.create(context.operations.get_bind(), checkfirst=False)
    inspector = Inspector(context.operations_connection)
    tables = ['elections', 'election_compounds', 'votes', 'archived_results']
    for table in tables:
        if table in inspector.get_table_names(context.schema):
            context.operations.execute(
                f'ALTER TABLE {table} '
                f'ALTER COLUMN domain TYPE _domain_of_influence '
                f'USING domain::text::_domain_of_influence'
            )

    # Drop old one
    old_type.drop(context.operations.get_bind(), checkfirst=False)

    # Change temporary to new one with the right name
    new_type = Enum(*new, name='domain_of_influence')
    new_type.create(context.operations.get_bind(), checkfirst=False)
    for table in tables:
        context.operations.execute(
            f'ALTER TABLE {table} '
            f'ALTER COLUMN domain TYPE domain_of_influence '
            f'USING domain::text::domain_of_influence'
        )
    # Drop temporary
    tmp_type.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Rename yays to yeas')
def rename_yays_to_yeas(context: UpgradeContext) -> None:
    if not context.has_column('ballot_results', 'yeas'):
        context.operations.alter_column(
            'ballot_results', 'yays', new_column_name='yeas'
        )


@upgrade_task('Add shortcode column')
def add_shortcode_column(context: UpgradeContext) -> None:
    if not context.has_column('votes', 'shortcode'):
        context.operations.add_column('votes', Column('shortcode', Text()))


@upgrade_task('Enable translation of vote title')
def enable_translation_of_vote_title(context: UpgradeContext) -> None:
    if context.has_column('votes', 'title'):
        context.operations.drop_column('votes', 'title')
    if not context.has_column('votes', 'title_translations'):
        context.operations.add_column('votes', Column(
            'title_translations', HSTORE, nullable=False
        ))


@upgrade_task('Add absolute majority column')
def add_absolute_majority_column(context: UpgradeContext) -> None:
    if not context.has_column('elections', 'absolute_majority'):
        context.operations.add_column(
            'elections',
            Column('absolute_majority', Integer())
        )


@upgrade_task('Add meta data')
def add_meta_data_columns(context: UpgradeContext) -> None:
    if not context.has_column('elections', 'meta'):
        context.operations.add_column('elections', Column('meta', JSON()))

    if not context.has_column('votes', 'meta'):
        context.operations.add_column('votes', Column('meta', JSON()))


@upgrade_task('Add municipality domain of influence')
def add_municipality_domain(context: UpgradeContext) -> None:
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

    # Add the new domain,
    alter_domain_of_influence(
        context,
        ['federation', 'canton'],
        ['federation', 'canton', 'municipality']
    )


@upgrade_task('Add party resuts columns')
def add_party_results_columns(context: UpgradeContext) -> None:
    if not context.has_column('party_results', 'color'):
        context.operations.add_column(
            'party_results',
            Column('color', Text())
        )

    if not context.has_column('party_results', 'year'):
        context.operations.add_column(
            'party_results',
            Column('year', Integer())
        )

    if not context.has_column('party_results', 'total_votes'):
        context.operations.add_column(
            'party_results',
            Column('total_votes', Integer())
        )


@upgrade_task('Add status')
def add_status_columns(context: UpgradeContext) -> None:
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
def add_candidate_party_column(context: UpgradeContext) -> None:
    for table in ['candidates', 'candiates']:
        if context.has_table(table):
            if not context.has_column(table, 'party'):
                context.operations.add_column(
                    table,
                    Column('party', Text, nullable=True)
                )


@upgrade_task('Rename candidates tables')
def rename_candidates_tables(context: UpgradeContext) -> None:
    for old_name, new_name in (
        ('candiate_results', 'candidate_results'),
        ('candiates', 'candidates'),
    ):
        if context.has_table(old_name):
            if context.has_table(new_name):
                context.operations.drop_table(new_name)
            context.operations.rename_table(old_name, new_name)


@upgrade_task('Adds ballot title')
def add_ballot_title(context: UpgradeContext) -> None:
    if not context.has_column('ballots', 'title_translations'):
        context.operations.add_column('ballots', Column(
            'title_translations', HSTORE, nullable=True
        ))


@upgrade_task('Add content columns')
def add_content_columns(context: UpgradeContext) -> None:
    if not context.has_column('elections', 'content'):
        context.operations.add_column('elections', Column('content', JSON))

    if not context.has_column('votes', 'content'):
        context.operations.add_column('votes', Column('content', JSON))


@upgrade_task('Add vote type column')
def add_vote_type_column(context: UpgradeContext) -> None:
    if not context.has_column('votes', 'type'):
        context.operations.add_column('votes', Column('type', Text))


@upgrade_task('Change election type column')
def change_election_type_column(context: UpgradeContext) -> None:
    type_ = Enum('proporz', 'majorz', name='type_of_election')
    context.operations.execute(
        'ALTER TABLE elections ALTER COLUMN type TYPE Text'
    )
    type_.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Replaces results group with name and district')
def replace_results_group(context: UpgradeContext) -> None:
    for table in ('ballot_results', 'election_results'):
        if (
            context.has_column(table, 'group')
            and not context.has_column(table, 'name')
        ):
            context.operations.alter_column(
                table, 'group', new_column_name='name'
            )
        if not context.has_column(table, 'district'):
            context.operations.add_column(
                table, Column('district', Text, nullable=True)
            )


@upgrade_task('Change counted columns of elections')
def change_counted_columns_of_elections(context: UpgradeContext) -> None:
    if not context.has_column('election_results', 'counted'):
        context.operations.add_column(
            'election_results', Column(
                'counted', Boolean, nullable=False, server_default='TRUE'
            )
        )

    if context.has_column('elections', 'total_entities'):
        context.operations.drop_column('elections', 'total_entities')

    if context.has_column('elections', 'counted_entities'):
        context.operations.drop_column('elections', 'counted_entities')


@upgrade_task(
    'Add region domain of influence',
    requires='onegov.ballot:Add municipality domain of influence',
)
def add_region_domain(context: UpgradeContext) -> None:
    alter_domain_of_influence(
        context,
        ['federation', 'canton', 'municipality'],
        ['federation', 'region', 'canton', 'municipality'],
    )


@upgrade_task('Rename eligible voters columns')
def renmame_elegible_voters_columns(context: UpgradeContext) -> None:
    tables = (
        'elections', 'election_results', 'ballots', 'ballot_results', 'votes'
    )

    for table in tables:
        if context.has_column(table, 'elegible_voters'):
            context.operations.alter_column(
                table, 'elegible_voters', new_column_name='eligible_voters'
            )


@upgrade_task('Add party results to compounds')
def add_party_results_to_compounds(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'election_id'):
        context.operations.drop_constraint(
            'party_results_election_id_fkey',
            'party_results',
            type_='foreignkey'
        )
        context.operations.alter_column(
            'party_results',
            'election_id',
            new_column_name='owner'
        )


@upgrade_task('Add panachage results to compounds')
def add_panachage_results_to_compounds(context: UpgradeContext) -> None:
    if not context.has_column('panachage_results', 'owner'):
        context.operations.add_column(
            'panachage_results',
            Column('owner', Text())
        )
    if context.has_column('panachage_results', 'source_list_id'):
        context.operations.alter_column(
            'panachage_results',
            'source_list_id',
            new_column_name='source'
        )
    if context.has_column('panachage_results', 'target_list_id'):
        context.operations.drop_constraint(
            'panachage_results_target_list_id_fkey',
            'panachage_results',
            type_='foreignkey'
        )
        context.operations.execute(
            'ALTER TABLE panachage_results '
            'ALTER COLUMN target_list_id TYPE Text'
        )
        context.operations.alter_column(
            'panachage_results',
            'target_list_id',
            new_column_name='target'
        )


@upgrade_task(
    'Add update contraints',
    requires='onegov.ballot:Rename candidates tables',
)
def add_update_contraints(context: UpgradeContext) -> None:
    # We use SQL (rather than operations.xxx) so that we can drop and add
    # the constraints in one statement
    for ref, table in (
        ('vote', 'ballots'),
        # ('election', 'candidates'),
        ('election', 'election_results'),
        ('election', 'list_connections'),
        ('election', 'lists'),
    ):
        context.operations.execute(
            f'ALTER TABLE {table} '
            f'DROP CONSTRAINT {table}_{ref}_id_fkey, '
            f'ADD CONSTRAINT {table}_{ref}_id_fkey'
            f' FOREIGN KEY ({ref}_id) REFERENCES {ref}s (id)'
            f' ON UPDATE CASCADE'
        )

    # there was a typo
    context.operations.execute(
        'ALTER TABLE candidates '
        'DROP CONSTRAINT IF EXISTS candiates_election_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candidates_election_id_fkey, '
        'ADD CONSTRAINT candidates_election_id_fkey'
        ' FOREIGN KEY (election_id) REFERENCES elections (id)'
        ' ON UPDATE CASCADE'
    )


@upgrade_task('Migrate election compounds')
def migrate_election_compounds(context: UpgradeContext) -> None:
    if context.has_column('election_compounds', 'elections'):
        context.operations.drop_column('election_compounds', 'elections')


@upgrade_task('Adds a default majority type')
def add_default_majority_type(context: UpgradeContext) -> None:
    # Removed data migrations
    pass


@upgrade_task('Add delete contraints')
def add_delete_contraints(context: UpgradeContext) -> None:
    # We use SQL (rather than operations.xxx) so that we can drop and add
    # the constraints in one statement
    for table, ref, do_update, do_delete in (
        # ('candidate_results', 'candidate', False, True),  # see below
        # ('candidate_results', 'election_result', False, True),  # see below
        ('candidates', 'election', True, True),
        # ('candidates', 'list', False, True),  # see below
        ('election_results', 'election', True, True),
        ('list_connections', 'election', True, True),
        ('list_results', 'election_result', False, True),
        ('list_results', 'list', False, True),
        # ('lists', 'connection', False, True),  # see below
        ('lists', 'election', True, True),
        ('ballot_results', 'ballot', False, True),
    ):
        update = 'ON UPDATE CASCADE' if do_update else ''
        delete = 'ON DELETE CASCADE' if do_delete else ''
        context.operations.execute(
            f'ALTER TABLE {table} '
            f'DROP CONSTRAINT {table}_{ref}_id_fkey, '
            f'ADD CONSTRAINT {table}_{ref}_id_fkey'
            f' FOREIGN KEY ({ref}_id) REFERENCES {ref}s (id) {update} {delete}'
        )

    # there was a typo
    context.operations.execute(
        'ALTER TABLE candidate_results '
        'DROP CONSTRAINT IF EXISTS candiate_results_candiate_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candiate_results_candidate_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candidate_results_candiate_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candidate_results_candidate_id_fkey, '
        'ADD CONSTRAINT candidate_results_candidate_id_fkey'
        ' FOREIGN KEY (candidate_id) REFERENCES candidates (id)'
        ' ON DELETE CASCADE'
    )
    context.operations.execute(
        'ALTER TABLE candidate_results '
        'DROP CONSTRAINT IF EXISTS candiate_results_election_result_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candidate_results_election_result_id_fkey,'
        ' ADD CONSTRAINT candidate_results_election_result_id_fkey'
        ' FOREIGN KEY (election_result_id) REFERENCES election_results (id)'
        ' ON DELETE CASCADE'
    )
    context.operations.execute(
        'ALTER TABLE candidates '
        'DROP CONSTRAINT IF EXISTS candiates_list_id_fkey, '
        'DROP CONSTRAINT IF EXISTS candidates_list_id_fkey,'
        ' ADD CONSTRAINT candidates_list_id_fkey'
        ' FOREIGN KEY (list_id) REFERENCES lists (id)'
        ' ON DELETE CASCADE'
    )

    # this one does not fit the schema
    context.operations.execute(
        'ALTER TABLE lists '
        'DROP CONSTRAINT IF EXISTS lists_connection_id_fkey,'
        ' ADD CONSTRAINT lists_connection_id_fkey'
        ' FOREIGN KEY (connection_id) REFERENCES list_connections (id)'
        ' ON DELETE CASCADE'
    )


@upgrade_task('Adds migration for related link and related link label')
def add_related_link_and_label(context: UpgradeContext) -> None:
    # Removed data migrations
    pass


@upgrade_task('Adds Doppelter Pukelsheim to CompoundElection/Election')
def add_after_pukelsheim(context: UpgradeContext) -> None:
    for table in ('election_compounds', 'elections'):
        if not context.has_column(table, 'after_pukelsheim'):
            context.add_column_with_defaults(
                table, Column(
                    'after_pukelsheim',
                    Boolean,
                    nullable=False,
                    default=False
                ), default=lambda x: False)

    if not context.has_column('election_compounds', 'pukelsheim_completed'):
        context.add_column_with_defaults(
            'election_compounds', Column(
                'pukelsheim_completed',
                Boolean,
                nullable=False,
                default=False
            ), default=lambda x: False)


@upgrade_task(
    'Add district and none domains of influence',
    requires='onegov.ballot:Add region domain of influence',
)
def add_district_and_none_domain(context: UpgradeContext) -> None:
    alter_domain_of_influence(
        context,
        ['federation', 'region', 'canton', 'municipality'],
        ['federation', 'canton', 'region', 'district', 'municipality', 'none']
    )


@upgrade_task('Adds last result change columns')
def add_last_result_change(context: UpgradeContext) -> None:
    for table in ('elections', 'election_compounds', 'votes'):
        if not context.has_column(table, 'last_result_change'):
            context.operations.add_column(
                table, Column('last_result_change', UTCDateTime)
            )


@upgrade_task('Adds voters count to party results')
def add_voters_count(context: UpgradeContext) -> None:
    if not context.has_column('party_results', 'voters_count'):
        context.operations.add_column(
            'party_results', Column('voters_count', Integer)
        )


@upgrade_task(
    'Cleans up pukelsheim fields',
    requires=(
        'onegov.ballot:Adds Doppelter Pukelsheim to CompoundElection/Election'
    )
)
def cleanup_pukelsheim_fields(context: UpgradeContext) -> None:
    if context.has_column('elections', 'after_pukelsheim'):
        context.operations.drop_column(
            'elections',
            'after_pukelsheim'
        )

    if context.has_column('election_compounds', 'after_pukelsheim'):
        context.operations.alter_column(
            'election_compounds',
            'after_pukelsheim',
            new_column_name='pukelsheim'
        )


@upgrade_task(
    'Add manual completion fields',
    requires=(
        'onegov.ballot:Cleans up pukelsheim fields'
    )
)
def add_manual_completion_fields(context: UpgradeContext) -> None:
    if not context.has_column('election_compounds', 'completes_manually'):
        context.add_column_with_defaults(
            'election_compounds',
            Column(
                'completes_manually',
                Boolean,
                nullable=False,
                default=False
            ),
            default=lambda x: False
        )

    if context.has_column('election_compounds', 'pukelsheim_completed'):
        context.operations.alter_column(
            'election_compounds',
            'pukelsheim_completed',
            new_column_name='manually_completed'
        )


@upgrade_task(
    'Change voters count to numeric',
    requires=(
        'onegov.ballot:Adds voters count to party results'
    )
)
def change_voters_count_to_numeric(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'voters_count'):
        context.operations.alter_column(
            'party_results',
            'voters_count',
            type_=Numeric(12, 2)
        )


@upgrade_task('Adds superregion to election results')
def add_superregion_to_election_results(context: UpgradeContext) -> None:
    if not context.has_column('election_results', 'superregion'):
        context.operations.add_column(
            'election_results', Column('superregion', Text, nullable=True)
        )


@upgrade_task('Adds total voters count to party results')
def add_total_voters_count(context: UpgradeContext) -> None:
    if not context.has_column('party_results', 'total_voters_count'):
        context.operations.add_column(
            'party_results', Column('total_voters_count', Numeric(12, 2))
        )


@upgrade_task(
    'Change total voters count to percentage',
    requires='onegov.ballot:Adds total voters count to party results',
)
def change_total_voters_count(context: UpgradeContext) -> None:
    if (
        context.has_column('party_results', 'total_voters_count')
        and not context.has_column('party_results', 'voters_count_percentage')
    ):
        context.operations.alter_column(
            'party_results', 'total_voters_count',
            new_column_name='voters_count_percentage'
        )


@upgrade_task('Add party id column')
def add_party_id_column(context: UpgradeContext) -> None:
    if not context.has_column('party_results', 'party_id'):
        context.operations.add_column(
            'party_results',
            Column('party_id', Text())
        )


@upgrade_task('Add party name translations')
def add_party_name_translations(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'name'):
        context.operations.alter_column(
            'party_results', 'name',
            nullable=True
        )

    if not context.has_column('party_results', 'name_translations'):
        context.add_column_with_defaults(
            table='party_results',
            column=Column('name_translations', HSTORE, nullable=False),
            default=lambda x: {}
        )

    if (
        context.has_column('party_results', 'name_translations')
        and context.has_column('party_results', 'name')
    ):
        context.operations.execute("""
            UPDATE party_results SET name_translations = hstore('de_CH', name);
        """)


@upgrade_task(
    'Remove obsolete party names',
    requires='onegov.ballot:Add party name translations',
)
def remove_obsolete_party_names(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'name'):
        context.operations.drop_column('party_results', 'name')

    if context.has_column('party_results', 'party_id'):
        context.operations.execute("""
            DELETE FROM party_results WHERE party_id is NULL;
        """)

        context.operations.alter_column(
            'party_results', 'party_id', nullable=False
        )


@upgrade_task('Add gender column')
def add_gender_column(context: UpgradeContext) -> None:
    if not context.has_column('candidates', 'gender'):
        context.operations.add_column(
            'candidates',
            Column(
                'gender',
                Enum('male', 'female', 'undetermined',
                     name='candidate_gender'),
                nullable=True
            )
        )


@upgrade_task('Add year of birth column')
def add_year_of_birth_column(context: UpgradeContext) -> None:
    if not context.has_column('candidates', 'year_of_birth'):
        context.operations.add_column(
            'candidates',
            Column('year_of_birth', Integer(), nullable=True)
        )


@upgrade_task('Add exapts columns')
def add_exapts_columns(context: UpgradeContext) -> None:
    for table in ('election_results', 'ballot_results'):
        if not context.has_column(table, 'expats'):
            context.operations.add_column(
                table,
                Column('expats', Integer(), nullable=True)
            )


@upgrade_task('Add domain columns to party results')
def add_domain_columns_to_party_results(context: UpgradeContext) -> None:
    for column in ('domain', 'domain_segment'):
        if not context.has_column('party_results', column):
            context.operations.add_column(
                'party_results',
                Column(column, Text(), nullable=True)
            )


@upgrade_task(
    'Drop party color column',
    requires='onegov.ballot:Add party resuts columns',
)
def drop_party_color_column(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'color'):
        context.operations.drop_column('party_results', 'color')


@upgrade_task(
    'Add foreign keys to party results',
    requires='onegov.ballot:Add party results to compounds'
)
def add_foreign_keys_to_party_results(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'owner'):
        context.operations.alter_column(
            'party_results', 'owner', nullable=True
        )

    if not context.has_column('party_results', 'election_id'):
        context.operations.add_column(
            'party_results',
            Column(
                'election_id',
                Text,
                ForeignKey(
                    'elections.id',
                    onupdate='CASCADE',
                    ondelete='CASCADE'
                ),
                nullable=True
            )
        )

    if not context.has_column('party_results', 'election_compound_id'):
        context.operations.add_column(
            'party_results',
            Column(
                'election_compound_id',
                Text,
                ForeignKey(
                    'election_compounds.id',
                    onupdate='CASCADE',
                    ondelete='CASCADE'
                ),
                nullable=True
            )
        )


@upgrade_task(
    'Add foreign keys to panachage results',
    requires='onegov.ballot:Add panachage results to compounds'
)
def add_foreign_keys_to_panahcage_results(context: UpgradeContext) -> None:
    if not context.has_column('panachage_results', 'election_id'):
        context.operations.add_column(
            'panachage_results',
            Column(
                'election_id',
                Text,
                ForeignKey(
                    'elections.id',
                    onupdate='CASCADE',
                    ondelete='CASCADE'
                ),
                nullable=True
            )
        )
    if not context.has_column('panachage_results', 'election_compound_id'):
        context.operations.add_column(
            'panachage_results',
            Column(
                'election_compound_id',
                Text,
                ForeignKey(
                    'election_compounds.id',
                    onupdate='CASCADE',
                    ondelete='CASCADE'
                ),
                nullable=True
            )
        )


@upgrade_task(
    'Drop owner from party results',
    requires='onegov.ballot:Add foreign keys to party results'
)
def drop_owner_from_party_results(context: UpgradeContext) -> None:
    if context.has_column('party_results', 'owner'):
        context.operations.drop_column(
            'party_results', 'owner'
        )


@upgrade_task(
    'Drop owner from panachage results',
    requires='onegov.ballot:Add foreign keys to panachage results'
)
def drop_owner_from_panachage_results(context: UpgradeContext) -> None:
    if context.has_column('panachage_results', 'owner'):
        context.operations.drop_column(
            'panachage_results', 'owner'
        )


@upgrade_task('Add type to election relationships')
def add_type_election_relationships(context: UpgradeContext) -> None:
    if context.has_table('election_associations'):
        if context.has_table('election_relationships'):
            context.operations.drop_table('election_relationships')
        context.operations.rename_table(
            'election_associations', 'election_relationships'
        )

    if context.has_table('election_relationships'):
        if not context.has_column('election_relationships', 'type'):
            context.operations.add_column(
                'election_relationships',
                Column('type', Text(), nullable=True)
            )


@upgrade_task('Remove old panachage results')
def remove_old_panachage_results(context: UpgradeContext) -> None:
    if context.has_table('panachage_results'):
        context.operations.drop_table('panachage_results')


@upgrade_task('Fix file constraints')
def fix_file_constraints(context: UpgradeContext) -> None:

    for table, ref in (
        ('files_for_elections_files', 'elections'),
        ('files_for_election_compounds_files', 'election_compounds'),
        ('files_for_votes_files', 'votes'),
    ):
        context.operations.execute(
            f'ALTER TABLE {table} '
            f'DROP CONSTRAINT {table}_{ref}_id_fkey, '
            f'ADD CONSTRAINT {table}_{ref}_id_fkey'
            f' FOREIGN KEY ({ref}_id) REFERENCES {ref} (id) ON UPDATE CASCADE'
        )


@upgrade_task('Add external ids')
def add_external_ids(context: UpgradeContext) -> None:
    for table in ('elections', 'election_compounds', 'votes'):
        if not context.has_column(table, 'external_id'):
            context.operations.add_column(
                table,
                Column('external_id', Text(), nullable=True)
            )


@upgrade_task('Add external ballot ids')
def add_external_ballot_ids(context: UpgradeContext) -> None:
    if not context.has_column('ballots', 'external_id'):
        context.operations.add_column(
            'ballots',
            Column('external_id', Text(), nullable=True)
        )


@upgrade_task('Change nullable of various ballot models')
def change_nullable_ballot(context: UpgradeContext) -> None:
    for table, column in (
        ('elections', 'type'),
        ('votes', 'type'),
        ('election_relationships', 'source_id'),
        ('election_compound_relationships', 'source_id'),
        ('election_compound_associations', 'election_compound_id')
    ):
        if context.has_column(table, column):
            context.operations.alter_column(table, column, nullable=False)
