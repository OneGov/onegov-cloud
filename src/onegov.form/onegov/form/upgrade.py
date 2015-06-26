""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.upgrade import upgrade_task
from sqlalchemy import Text


@upgrade_task(name="Convert submission_files.id to text")
def convert_submission_files_id_to_text(context):
    context.operations.alter_column('submission_files', 'id', type_=Text)
