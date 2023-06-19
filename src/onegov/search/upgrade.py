""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.orm import Base
from onegov.core.upgrade import upgrade_task
from onegov.search.utils import searchable_sqlalchemy_models


@upgrade_task('Adding full text search index column to postgres 40')
def adding_full_text_search_columns_to_postgres(context):
    print("*** tschupre upgrading to postgres")
    # need to create all indexes in postgresql on every model in project
    # for full text search. This will make elastic search setup obsolete.
    # Ticket reference: ogc-508
    #
    # NOTE: This task can only be removed once all production systems got
    # this upgrade
    #
    # onegov-core --select /onegov_org/risch upgrade
    # onegov-core --select /onegov_org/* upgrade
    # onegov-core --select /onegov_town6/meggen upgrade
    # onegov-core --select /onegov_town6/* upgrade

    session = context.session
    schema = context.schema

    for model in searchable_sqlalchemy_models(Base):
        print(f'*** model to migrate: {model}')
        if model.__tablename__ in ['users', 'events']:
            model.add_fts_column(session, schema)

    # def generate_email():
    #     import random
    #     validchars = 'abcdefghijklmnopqrstuvwxyz1234567890'
    #     loginlen = random.randint(4, 15)
    #     login = ''
    #     for i in range(loginlen):
    #         pos = random.randint(0, len(validchars) - 1)
    #         login = login + validchars[pos]
    #     if login[0].isnumeric():
    #         pos = random.randint(0, len(validchars) - 10)
    #         login = validchars[pos] + login
    #     servers = ['@meggen']
    #     servpos = random.randint(0, len(servers) - 1)
    #     email = login + servers[servpos]
    #     tlds = ['.ch']
    #     tldpos = random.randint(0, len(tlds) - 1)
    #     email = email + tlds[tldpos]
    #     return email
    #
    # def generate_users(count=1000):
    #     users = list()
    #
    #     for i in range(count):
    #         users.append(
    #             User(
    #                 username=generate_email(),
    #                 password_hash='test_password',
    #                 role='member'
    #             )
    #         )
    #     return users

    # click.secho('Adding users...')
    # for user in generate_users(10000):
    #     context.session.add(user)
