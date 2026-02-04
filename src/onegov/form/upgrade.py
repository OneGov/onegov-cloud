""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

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
from sqlalchemy import Column, Integer, Text, text
from sqlalchemy.engine.reflection import Inspector


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Enable external form submissions')
def enable_external_form_submissions(context: UpgradeContext) -> None:

    context.operations.alter_column('submissions', 'name', nullable=True)


@upgrade_task('Set payment method for existing forms')
def set_payment_method_for_existing_forms(context: UpgradeContext) -> None:
    forms = FormDefinitionCollection(context.session)

    for form in forms.query():
        form.payment_method = 'manual'


@upgrade_task('Migrate form submission files to onegov.file')
def migrate_form_submission_files_to_onegov_file(
    context: UpgradeContext
) -> None:
    submission_ids = [
        row[0] for row in
        context.session.execute(text("""
            SELECT submission_id
            FROM submission_files
        """))
    ]

    if not submission_ids:
        return

    submissions = {
        s.id: s for s in
        context.session.query(FormSubmission).filter(
            FormSubmission.id.in_(submission_ids)
        )
    }

    for row in context.session.execute(text("""
        SELECT submission_id, field_id, filedata
        FROM submission_files
    """)):
        submission_id, field_id, filedata = row
        submission = submissions[submission_id]

        replacement = FormFile(  # type:ignore[misc]
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
        submission.data.changed()  # type:ignore[attr-defined]

        submission.files.append(replacement)

    context.session.flush()
    context.session.execute(text('DROP TABLE IF EXISTS submission_files'))


@upgrade_task('Add payment_method to definitions and submissions')
def add_payment_method_to_definitions_and_submissions(
    context: UpgradeContext
) -> None:

    context.add_column_with_defaults(
        table='forms',
        column=Column('payment_method', Text, nullable=False),
        default=lambda form: form.content.get('payment_method', 'manual')
    )

    context.add_column_with_defaults(
        table='submissions',
        column=Column('payment_method', Text, nullable=False),
        default=lambda submission: (
            submission.form
            and submission.form.content.get('payment_method', 'manual')
            or 'manual'
        )
    )

    for form in context.records_per_table('forms'):
        form.content.pop('payment_method', None)


@upgrade_task('Add meta dictionary to submissions')
def add_meta_directory_to_submissions(context: UpgradeContext) -> None:

    context.add_column_with_defaults(
        table='submissions',
        column=Column('meta', JSON, nullable=False),
        default=lambda submission: {}
    )


@upgrade_task('Add group/order to form definitions')
def add_group_order_to_form_definitions(context: UpgradeContext) -> None:

    context.operations.add_column('forms', Column(
        'group', Text, nullable=True
    ))

    context.add_column_with_defaults(
        table='forms',
        column=Column('order', Text, nullable=False, index=True),
        default=lambda form: normalize_for_url(form.title)
    )


@upgrade_task('Add registration window columns')
def add_registration_window_columns(context: UpgradeContext) -> None:
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


@upgrade_task('Make form polymorphic type non-nullable')
def make_form_polymorphic_type_non_nullable(context: UpgradeContext) -> None:
    if context.has_table('forms'):
        context.operations.execute(text("""
            UPDATE forms SET type = 'generic' WHERE type IS NULL;
        """))

        context.operations.alter_column('forms', 'type', nullable=False)


@upgrade_task('Add title to submission windows')
def add_title_to_submission_windows(context: UpgradeContext) -> None:
    if not context.has_column('submission_windows', 'title'):
        context.add_column_with_defaults(
            'submission_windows',
            Column(
                'title',
                Text,
                nullable=True
            ),
            default=None
        )


@upgrade_task('Remove no overlapping submission windows constraint')
def remove_no_overlapping_submission_windows_constraint(
    context: UpgradeContext
) -> None:
    if not context.has_table('submission_windows'):
        return

    inspector = Inspector(context.operations_connection)
    # Check unique constraints
    unique_constraints = inspector.get_unique_constraints('submission_windows')
    # Check check constraints
    check_constraints = inspector.get_check_constraints('submission_windows')

    constraint_exists = any(
        const['name'] == 'no_overlapping_submission_windows'
        for const in unique_constraints + check_constraints
    )

    if constraint_exists:
        context.operations.drop_constraint(
            'no_overlapping_submission_windows',
            'submission_windows'
        )


@upgrade_task('Remove state column form survey submissions')
def remove_state_from_survey_submissions(context: UpgradeContext) -> None:
    if context.has_table('survey_submissions'):
        if context.has_column('survey_submissions', 'state'):
            context.operations.drop_column('survey_submissions', 'state')
