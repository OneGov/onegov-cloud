""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from collections import defaultdict
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import JSON, UUID
from onegov.user import User, UserCollection
from sqlalchemy import Boolean, Column, Text
from sqlalchemy.sql import text


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


def change_ownership_by_name(context, old_username, new_username):
    # transfer all ownership without using models (which might or
    # might not be available here)
    if context.has_table('activities'):
        context.operations.execute("""
            UPDATE activities
            SET username = '{new_username}'
            WHERE username = '{old_username}'
        """.format(new_username=new_username, old_username=old_username))

    if context.has_table('attendees'):
        context.operations.execute("""
            UPDATE attendees
            SET username = '{new_username}'
            WHERE username = '{old_username}'
        """.format(new_username=new_username, old_username=old_username))

    if context.has_table('bookings'):
        context.operations.execute("""
            UPDATE bookings
            SET username = '{new_username}'
            WHERE username = '{old_username}'
        """.format(new_username=new_username, old_username=old_username))

    if context.has_table('invoice_items'):
        context.operations.execute("""
            UPDATE invoice_items
            SET username = '{new_username}'
            WHERE username = '{old_username}'
        """.format(new_username=new_username, old_username=old_username))


def change_ownership_by_id(context, old_userid, new_userid):
    if context.has_table('tickets'):
        context.operations.execute("""
            UPDATE tickets
            SET user_id = '{new_userid}'
            WHERE user_id = '{old_userid}'
        """.format(old_userid=old_userid.hex, new_userid=new_userid.hex))


@upgrade_task('Force lowercase usernames')
def force_lowercase_usernames(context):
    users = defaultdict(list)

    for user in context.session.query(User).all():
        users[user.username.lower()].append(user)

    temp_user = UserCollection(context.session).add(
        username='temp',
        password='temp',
        active=False,
        role='member',
    )

    for username, users in users.items():

        # simply change usernames that don't conflict with others
        if len(users) == 1:
            with context.session.no_autoflush:
                change_ownership_by_name(
                    context, users[0].username, 'temp')

                users[0].username = users[0].username.lower()
                context.session.flush()

                change_ownership_by_name(
                    context, 'temp', users[0].username)

            continue

        # from others select one user, move ownership to it and then
        # remove the other users -> that means that some of our users need
        # to reset their password...

        # the remaining user is selected by activity, last-change and role
        # we prefer active users over low-ranking users over less recently
        # updated users
        role_hierarchy = [
            'member',
            'editor',
            'admin'
        ]

        def sort_key(user):
            return (
                user.active,
                role_hierarchy.index(user.role),
                user.last_change,
            )

        remaining = sorted(users, key=sort_key)[-1]
        remaining_data = remaining.data or {}

        others = [u for u in users if u.id != remaining.id]

        for other in others:

            # keep as much user data as possible
            for key, value in (other.data or {}).items():
                if value and not remaining.data.get(key):
                    remaining_data[key] = value

            # change the userids
            change_ownership_by_id(context, other.id, remaining.id)

            # change the username
            change_ownership_by_name(context, other.username, 'temp')

            # delete the other user
            context.operations.execute("""
                DELETE from users
                WHERE id = '{}'
            """.format(other.id.hex))

        # switch the remaining user
        change_ownership_by_name(context, remaining.username, 'temp')

        remaining.username = remaining.username.lower()
        remaining.data = remaining_data
        context.session.flush()

        change_ownership_by_name(context, 'temp', remaining.username)

    # enforce the lowercase rule
    context.operations.create_index(
        'lowercase_username', 'users', [
            text('lower("username")')
        ], unique=True
    )

    # remove the temporary user
    context.session.delete(temp_user)


@upgrade_task('Add singup_token column')
def add_signup_token_column(context):
    context.operations.add_column(
        'users', Column('signup_token', Text, nullable=True))


@upgrade_task('Add group_id column')
def add_group_id_column(context):
    if not context.has_column('users', 'group_id'):
        context.operations.add_column(
            'users',
            Column('group_id', UUID, nullable=True)
        )


@upgrade_task('Add type column')
def add_type_column(context):
    if not context.has_column('users', 'type'):
        context.operations.add_column(
            'users',
            Column('type', Text, nullable=True)
        )


@upgrade_task('Add authentication_provider column')
def add_authentication_provider_column(context):
    context.operations.add_column(
        'users', Column('authentication_provider', JSON, nullable=True))
