""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import JSON
from onegov.user import User
from sqlalchemy import Boolean, Column, Text


@upgrade_task('Add second_factor column')
def add_second_factor_column(context):
    context.operations.add_column(
        'users', Column('second_factor', JSON, nullable=True)
    )


@upgrade_task('Add active column')
def add_active_column(context):
    context.operations.add_column(
        'users', Column('active', Boolean, nullable=True, default=True)
    )

    for user in context.session.query(User).all():
        user.active = True

    context.session.flush()
    context.operations.alter_column('users', 'active', nullable=False)


@upgrade_task('Add realname column')
def add_realname_column(context):
    context.operations.add_column(
        'users', Column('realname', Text, nullable=True))

    for user in context.session.query(User).all():
        user.realname = (user.data and user.data or {}).get('name')

    context.session.flush()
