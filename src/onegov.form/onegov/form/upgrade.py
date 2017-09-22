""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from depot.io.utils import FileIntent
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import dictionary_to_binary
from onegov.form import FormDefinitionCollection
from onegov.form import FormFile
from onegov.form import FormSubmission


@upgrade_task('Enable external form submissions')
def enable_external_form_submissions(context):

    context.operations.alter_column('submissions', 'name', nullable=True)


@upgrade_task('Set payment method for existing forms')
def set_payment_method_for_existing_forms(context):
    forms = FormDefinitionCollection(context.session)

    for form in forms.query():
        form.payment_method = 'manual'


@upgrade_task('Migrate form submission files to onegov.file')
def migrate_form_submission_files_to_onegov_file(context):
    submission_ids = [
        row[0] for row in
        context.session.execute("""
            SELECT submission_id
            FROM submission_files
        """)
    ]

    if not submission_ids:
        return

    submissions = {
        s.id: s for s in
        context.session.query(FormSubmission).filter(
            FormSubmission.id.in_(submission_ids)
        )
    }

    for row in context.session.execute("""
        SELECT submission_id, field_id, filedata
        FROM submission_files
    """):
        submission_id, field_id, filedata = row
        submission = submissions[submission_id]

        replacement = FormFile(
            id=random_token(),
            name=submission.data[field_id]['filename'],
            note=field_id,
            reference=FileIntent(
                BytesIO(dictionary_to_binary({'data': filedata})),
                submission.data[field_id]['filename'],
                submission.data[field_id]['mimetype'],
            )
        )

        assert submission.data[field_id]['data'].startswith('@')

        submission.data[field_id]['data'] = '@' + replacement.id
        submission.data.changed()

        submission.files.append(replacement)

    context.session.flush()
    context.session.execute("DROP TABLE IF EXISTS submission_files")
