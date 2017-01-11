""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Election, Vote
from onegov.core.upgrade import upgrade_task
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult


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
                result.meta = result.meta or {}
                result.meta['id'] = vote.id

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
                result.meta = result.meta or {}
                result.meta['id'] = election.id
