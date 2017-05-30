""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.form import FormDefinitionCollection


@upgrade_task('Enable external form submissions')
def enable_external_form_submissions(context):

    context.operations.alter_column('submissions', 'name', nullable=True)


@upgrade_task('Set payment method for existing forms')
def set_payment_method_for_existing_forms(context):
    forms = FormDefinitionCollection(context.session)

    for form in forms.query():
        form.payment_method = 'manual'
