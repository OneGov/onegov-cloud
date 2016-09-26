""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.election_day.collections import ArchivedResultCollection


@upgrade_task('Create archived results')
def create_archived_results(context):

    """ Create an initial archived result entry for all existing votes
    and elections.

    Because we don't have a real request here, the generated URL are wrong!
    To fix the links, login after the update and call the 'update-results'
    view.

    """
    ArchivedResultCollection(context.session).update_all(context.request)
