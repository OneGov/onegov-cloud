from onegov.core.upgrade import upgrade_task
from sqlalchemy import Enum


@upgrade_task('Adds accepted state')
def add_accepted_state(context):
    # Create a temporary definition and use it
    tmp_type = Enum(
        'drafted', 'submitted', 'published', 'rejected', 'accepted',
        name='_official_notice_state'
    )
    tmp_type.create(context.operations.get_bind(), checkfirst=False)
    context.operations.execute(
        'ALTER TABLE official_notices ALTER COLUMN state '
        'TYPE _official_notice_state '
        'USING state::text::_official_notice_state'
    )

    # Drop the old definition
    old_type = Enum(
        'drafted', 'submitted', 'published', 'rejected',
        name='official_notice_state'
    )
    old_type.drop(context.operations.get_bind(), checkfirst=False)

    # Create the new definition and use it
    new_type = Enum(
        'drafted', 'submitted', 'published', 'rejected', 'accepted',
        name='official_notice_state'
    )
    new_type.create(context.operations.get_bind(), checkfirst=False)

    context.operations.execute(
        'ALTER TABLE official_notices ALTER COLUMN state '
        'TYPE official_notice_state '
        'USING state::text::official_notice_state'
    )

    # Drop the temporary defintion
    tmp_type.drop(context.operations.get_bind(), checkfirst=False)
