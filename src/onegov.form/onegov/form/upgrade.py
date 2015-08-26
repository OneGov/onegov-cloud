""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task


@upgrade_task('Enable external form submissions')
def enable_external_form_submissions(context):

    context.operations.alter_column('submissions', 'name', nullable=True)
