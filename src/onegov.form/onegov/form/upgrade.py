""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from depot.io.utils import FileIntent
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.orm.types import JSON, UUID
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import dictionary_to_binary
from onegov.core.utils import normalize_for_url
from onegov.form import FormDefinitionCollection
from onegov.form import FormFile
from onegov.form import FormSubmission
from sqlalchemy import Column, Integer, Text


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


@upgrade_task('Add payment_method to definitions and submissions')
def add_payment_method_to_definitions_and_submissions(context):

    context.add_column_with_defaults(
        table='forms',
        column=Column('payment_method', Text, nullable=False),
        default=lambda form: form.content.get('payment_method', 'manual')
    )

    context.add_column_with_defaults(
        table='submissions',
        column=Column('payment_method', Text, nullable=False),
        default=lambda submission: (
            submission.form and
            submission.form.content.get('payment_method', 'manual') or
            'manual'
        )
    )

    for form in context.records_per_table('forms'):
        form.content.pop('payment_method', None)


@upgrade_task('Add meta dictionary to submissions')
def add_meta_directory_to_submissions(context):

    context.add_column_with_defaults(
        table='submissions',
        column=Column('meta', JSON, nullable=False),
        default=lambda submission: dict()
    )


@upgrade_task('Add group/order to form definitions')
def add_group_order_to_form_definitions(context):

    context.operations.add_column('forms', Column(
        'group', Text, nullable=True
    ))

    context.add_column_with_defaults(
        table='forms',
        column=Column('order', Text, nullable=False, index=True),
        default=lambda form: normalize_for_url(form.title)
    )


@upgrade_task('Add registration window columns')
def add_registration_window_columns(context):
    context.operations.add_column(
        'submissions',
        Column('claimed', Integer, nullable=True)
    )

    context.operations.add_column(
        'submissions',
        Column('registration_window_id', UUID, nullable=True)
    )

    context.add_column_with_defaults(
        table='submissions',
        column=Column('spots', Integer, nullable=False),
        default=0
    )
