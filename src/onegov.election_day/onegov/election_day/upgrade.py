""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.core.orm.types import JSON
from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Subscriber
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import Text


@upgrade_task('Create archived results')
def create_archived_results(context):

    """ Create an initial archived result entry for all existing votes
    and elections.

    Because we don't have a real request here, the generated URL are wrong!
    To fix the links, login after the update and call the 'update-results'
    view.

    """
    ArchivedResultCollection(context.session).update_all(context.request)


@upgrade_task('Add ID to archived results')
def add_id_to_archived_results(context):

    """ Add the IDs of the elections/votes as meta information to the results.

    Normally, the right election and vote should be found. To be sure, you
    call the 'update-results' view to ensure that everything is right.
    """
    session = context.session

    results = session.query(ArchivedResult)
    results = results.filter(ArchivedResult.schema == context.app.schema)

    for result in results:
        if result.type == 'vote':
            vote = session.query(Vote).filter(
                Vote.date == result.date,
                Vote.domain == result.domain,
                Vote.shortcode == result.shortcode,
                Vote.title_translations == result.title_translations
            ).first()
            if vote and vote.id in result.url:
                result.external_id = vote.id

        if result.type == 'election':
            election = session.query(Election).filter(
                Election.date == result.date,
                Election.domain == result.domain,
                Election.shortcode == result.shortcode,
                Election.title_translations == result.title_translations,
                Election.counted_entities == result.counted_entities,
                Election.total_entities == result.total_entities,
            ).first()
            if election and election.id in result.url:
                result.external_id = election.id


@upgrade_task('Update vote progress')
def update_vote_progress(context):

    """ Recalculate the vote progress for the archived results.

    """
    session = context.session

    results = session.query(ArchivedResult)
    results = results.filter(
        ArchivedResult.schema == context.app.schema,
        ArchivedResult.type == 'vote'
    )

    for result in results:
        vote = session.query(Vote).filter_by(id=result.external_id)
        vote = vote.first()
        if vote:
            result.counted_entities, result.total_entities = vote.progress


@upgrade_task('Add elected candidates to archived results')
def add_elected_candidates(context):

    """ Adds the elected candidates to the archived results,

    """
    session = context.session

    results = session.query(ArchivedResult)
    results = results.filter(
        ArchivedResult.schema == context.app.schema,
        ArchivedResult.type == 'election'
    )

    for result in results:
        election = session.query(Election).filter_by(id=result.external_id)
        election = election.first()
        if election:
            result.elected_candidates = election.elected_candidates


@upgrade_task('Add content columns to archived results')
def add_content_columns_to_archived_results(context):
    if not context.has_column('archived_results', 'content'):
        context.operations.add_column(
            'archived_results', Column('content', JSON)
        )


@upgrade_task('Change last change columns')
def change_last_change_columns(context):
    if not context.has_column('archived_results', 'last_modified'):
        context.operations.add_column(
            'archived_results',
            Column('last_modified', UTCDateTime, nullable=True)
        )
    if context.has_column('archived_results', 'last_result_change'):
        context.operations.execute(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'archived_results', 'last_result_change'
            )
        )

    if (
        context.has_column('notifications', 'last_change') and
        not context.has_column('notifications', 'last_modified')
    ):
        context.operations.execute(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'notifications', 'last_change', 'last_modified'
            )
        )

    if context.has_column('notifications', 'last_modified'):
        context.operations.execute(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'notifications', 'last_modified'
            )
        )


@upgrade_task('Make subscriber polymorphic')
def make_subscriber_polymorphic(context):
    if not context.has_column('subscribers', 'type'):
        context.operations.add_column(
            'subscribers',
            Column('type', Text, nullable=True)
        )

    if (
        context.has_column('subscribers', 'phone_number') and
        not context.has_column('subscribers', 'address')
    ):
        context.operations.execute(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'subscribers', 'phone_number', 'address'
            )
        )

    if context.has_column('subscribers', 'type'):
        susbscribers = context.session.query(Subscriber)
        susbscribers = susbscribers.filter(Subscriber.type.is_(None))
        for subscriber in susbscribers:
            subscriber.type = 'sms'


@upgrade_task('Make notifications polymorphic')
def make_notifications_polymorphic(context):
    if (
        context.has_column('notifications', 'action') and
        not context.has_column('notifications', 'type')
    ):
        context.operations.execute(
            'ALTER TABLE {} RENAME COLUMN {} TO {};'.format(
                'notifications', 'action', 'type'
            )
        )
        context.operations.execute(
            'ALTER TABLE {} ALTER COLUMN {} DROP NOT NULL;'.format(
                'notifications', 'type'
            )
        )


@upgrade_task(
    'Apply static data',
    requires='onegov.ballot:Replaces results group with name and district'
)
def apply_static_data(context):
    principal = getattr(context.app, 'principal', None)
    if not principal:
        return

    for vote in context.session.query(Vote):
        for ballot in vote.ballots:
            assert vote.date and vote.date.year in principal.entities
            for result in ballot.results:
                assert (
                    result.entity_id in principal.entities[vote.date.year] or
                    result.entity_id == 0
                )
                result.name = principal.entities.\
                    get(vote.date.year, {}).\
                    get(result.entity_id, {}).\
                    get('name', '')
                result.district = principal.entities.\
                    get(vote.date.year, {}).\
                    get(result.entity_id, {}).\
                    get('district', '')

    for election in context.session.query(Election):
        assert election.date and election.date.year in principal.entities
        for result in election.results:
            assert (
                result.entity_id in principal.entities[election.date.year] or
                result.entity_id == 0
            )
            result.name = principal.entities.\
                get(election.date.year, {}).\
                get(result.entity_id, {}).\
                get('name', '')
            result.district = principal.entities.\
                get(election.date.year, {}).\
                get(result.entity_id, {}).\
                get('district', '')


@upgrade_task('Add election compound to archive')
def add_election_compound_to_archive(context):
    old_type = Enum('election', 'vote', name='type_of_result')
    new_type = Enum(
        'election', 'election_compound', 'vote', name='type_of_result'
    )
    tmp_type = Enum(
        'election', 'election_compound', 'vote', name='_type_of_result'
    )

    tmp_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(
        'ALTER TABLE archived_results ALTER COLUMN type '
        'TYPE _type_of_result USING type::text::_type_of_result'
    )

    old_type.drop(context.operations.get_bind(), checkfirst=False)

    new_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(
        'ALTER TABLE archived_results ALTER COLUMN type '
        'TYPE type_of_result USING type::text::type_of_result'
    )

    tmp_type.drop(context.operations.get_bind(), checkfirst=False)


@upgrade_task('Add contraints to notifications and sources')
def add_contraints_to_notifications_and_sources(context):
    # We use SQL (rather than operations.xxx) so that we can drop and add
    # the constraints in one statement
    for ref in ('election', 'vote'):
        for table in ('notifications', 'upload_data_source_item'):
            context.operations.execute(
                f'ALTER TABLE {table} '
                f'DROP CONSTRAINT {table}_{ref}_id_fkey, '
                f'ADD CONSTRAINT {table}_{ref}_id_fkey'
                f' FOREIGN KEY ({ref}_id) REFERENCES {ref}s (id)'
                f' ON UPDATE CASCADE'
            )
