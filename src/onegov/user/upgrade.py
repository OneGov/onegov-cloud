""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from collections import defaultdict
from onegov.core.upgrade import upgrade_task
from onegov.core.orm.types import JSON, UUID, UTCDateTime
from onegov.user import User, UserCollection
from sqlalchemy import Boolean, Column, Text
from sqlalchemy.sql import text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from onegov.core.upgrade import UpgradeContext


@upgrade_task('Add second_factor column')
def add_second_factor_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('second_factor', JSON, nullable=True)
    )


@upgrade_task('Add active column')
def add_active_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('active', Boolean, nullable=True, default=True)
    )

    for user in context.session.query(User).all():
        user.active = True

    context.session.flush()
    context.operations.alter_column('users', 'active', nullable=False)


@upgrade_task('Add realname column')
def add_realname_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('realname', Text, nullable=True))

    for user in context.session.query(User).all():
        user.realname = (user.data and user.data or {}).get('name')

    context.session.flush()


def change_ownership_by_name(
    context: UpgradeContext,
    old_username: str,
    new_username: str
) -> None:

    # transfer all ownership without using models (which might or
    # might not be available here)
    if context.has_table('activities'):
        context.operations.execute(text("""
            UPDATE activities
            SET username = :new_username
            WHERE username = :old_username
        """), {'new_username': new_username, 'old_username': old_username})

    if context.has_table('attendees'):
        context.operations.execute(text("""
            UPDATE attendees
            SET username = :new_username
            WHERE username = :old_username
        """), {'new_username': new_username, 'old_username': old_username})

    if context.has_table('bookings'):
        context.operations.execute(text("""
            UPDATE bookings
            SET username = :new_username
            WHERE username = :old_username
        """), {'new_username': new_username, 'old_username': old_username})

    if context.has_table('invoice_items'):
        context.operations.execute(text("""
            UPDATE invoice_items
            SET username = :new_username
            WHERE username = :old_username
        """), {'new_username': new_username, 'old_username': old_username})


def change_ownership_by_id(
    context: UpgradeContext,
    old_userid: uuid.UUID,
    new_userid: uuid.UUID
) -> None:
    if context.has_table('tickets'):
        context.operations.execute(text("""
            UPDATE tickets
            SET user_id = :new_userid
            WHERE user_id = :old_userid
        """), {'old_userid': old_userid, 'new_userid': new_userid})


@upgrade_task('Force lowercase usernames')
def force_lowercase_usernames(context: UpgradeContext) -> None:
    users = defaultdict(list)

    for user in context.session.query(User).all():
        users[user.username.lower()].append(user)

    temp_user = UserCollection(context.session).add(
        username='temp',
        password='temp',  # nosec: B106
        active=False,
        role='member',
    )

    for users_ in users.values():

        # simply change usernames that don't conflict with others
        if len(users_) == 1:
            with context.session.no_autoflush:
                change_ownership_by_name(
                    context, users_[0].username, 'temp')

                users_[0].username = users_[0].username.lower()
                context.session.flush()

                change_ownership_by_name(
                    context, 'temp', users_[0].username)

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

        def sort_key(
            user: User,
            role_hierarchy: list[str] = role_hierarchy
        ) -> tuple[bool, int, datetime]:
            return (
                user.active,
                role_hierarchy.index(user.role),
                user.last_change,
            )

        # FIXME: This never actually worked before because it was using the
        #        the dictionary instead of the list, was this maybe hotfixed
        #        and then just never merged into the codebase?
        remaining = max(users_, key=sort_key)
        remaining_data = remaining.data or {}

        others = [u for u in users_ if u.id != remaining.id]

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
            context.operations.execute(text("""
                DELETE from users
                WHERE id = :user_id
            """), {'user_id': other.id})

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
def add_signup_token_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('signup_token', Text, nullable=True))


@upgrade_task('Add group_id column')
def add_group_id_column(context: UpgradeContext) -> None:
    if not context.has_column('users', 'group_id'):
        context.operations.add_column(
            'users',
            Column('group_id', UUID, nullable=True)
        )


@upgrade_task('Add type column')
def add_type_column(context: UpgradeContext) -> None:
    if not context.has_column('users', 'type'):
        context.operations.add_column(
            'users',
            Column('type', Text, nullable=True)
        )


@upgrade_task('Add authentication_provider column')
def add_authentication_provider_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('authentication_provider', JSON, nullable=True))


@upgrade_task('Drop authentication_provider column')
def drop_authentication_provider_column(context: UpgradeContext) -> None:
    context.operations.drop_column('users', 'authentication_provider')


@upgrade_task('Add source column')
def add_source_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users',
        Column('source', Text, nullable=True, default=None)
    )


@upgrade_task('Add source_id column')
def add_source_id_column(context: UpgradeContext) -> None:
    context.operations.add_column(
        'users', Column('source_id', Text, nullable=True, default=None))

    context.operations.create_unique_constraint(
        'unique_source_id', 'users', ('source', 'source_id'))


@upgrade_task('Make user models polymorphic type non-nullable')
def make_user_models_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    for table in ('users', 'groups', 'role_mappings'):
        if context.has_table(table):
            context.operations.execute(text(f"""
                UPDATE {table} SET type = 'generic' WHERE type IS NULL;
            """))

            context.operations.alter_column(table, 'type', nullable=False)


@upgrade_task('Add scope column')
def add_scope_column(context: UpgradeContext) -> None:
    if not context.has_table('tans'):
        return

    context.operations.add_column(
        'tans', Column('scope', Text, nullable=True, index=True)
    )

    context.operations.execute(text(
        "UPDATE tans set scope = 'mtan_access' WHERE scope IS NULL;"
    ))

    context.session.flush()
    context.operations.alter_column('tans', 'scope', nullable=False)


@upgrade_task('Move users.group_id to association table')
def move_group_id_to_association_table(context: UpgradeContext) -> None:
    if not context.has_table('users'):
        return

    if not context.has_column('users', 'group_id'):
        return

    assert context.has_table('user_group_associations')

    context.operations.execute(text("""
        INSERT INTO user_group_associations
        SELECT id AS user_id, group_id
          FROM users
         WHERE group_id IS NOT NULL;
    """))

    context.session.flush()
    context.operations.drop_column('users', 'group_id')


@upgrade_task('Add last_login column')
def add_last_login_column(context: UpgradeContext) -> None:
    if not context.has_table('users'):
        return

    if not context.has_column('users', 'last_login'):
        context.operations.add_column(
            'users', Column('last_login', UTCDateTime, nullable=True)
        )

        # Pre-populate last_login from existing session data
        context.operations.execute(text("""
            UPDATE users
            SET last_login = subquery.max_timestamp::timestamp
            FROM (
                SELECT
                    id,
                    MAX(
                        (session_value->>'timestamp')::timestamp
                    ) as max_timestamp
                FROM
                    users,
                    LATERAL jsonb_each(data->'sessions')
                        AS session_entries(session_key, session_value)
                WHERE
                    data->'sessions' IS NOT NULL
                    AND jsonb_typeof(data->'sessions') = 'object'
                GROUP BY id
            ) AS subquery
            WHERE users.id = subquery.id;
        """))
