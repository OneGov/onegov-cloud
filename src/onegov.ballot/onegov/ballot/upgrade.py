""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.ballot import Vote
from onegov.core.orm.types import HSTORE
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column, Text


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
