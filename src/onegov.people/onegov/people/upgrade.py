""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Text


@upgrade_task('Rename academic_title to salutation')
def rename_academic_title_to_salutation(context):

    context.operations.alter_column(
        'people', 'academic_title', new_column_name='salutation')


@upgrade_task('Add function column')
def add_function_column(context):
    context.operations.add_column(
        'people', Column('function', Text, nullable=True))


@upgrade_task('Add notes column')
def add_notes_column(context):
    context.operations.add_column(
        'people', Column('notes', Text, nullable=True))


@upgrade_task('Add person type column')
def add_person_type_column(context):
    if not context.has_column('people', 'type'):
        context.operations.add_column('people', Column('type', Text))


@upgrade_task('Add meta data and content columns')
def add_meta_data_and_content_columns(context):
    if not context.has_column('people', 'meta'):
        context.operations.add_column('people', Column('meta', JSON()))

    if not context.has_column('people', 'content'):
        context.operations.add_column('people', Column('content', JSON))
