""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.core.upgrade import upgrade_task
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.core.orm.types import JSON
from sqlalchemy import Column


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
