""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from sqlalchemy.sql.expression import nullsfirst, text


@upgrade_task('Add parent order index')
def add_parent_order_index(context):
    context.operations.create_index(
        'page_order', 'pages', [
            text('"parent_id" NULLS FIRST'),
            text('"order" NULLS FIRST')
        ]
    )
