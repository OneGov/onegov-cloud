""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""

from onegov.core.orm import Base
from onegov.core.upgrade import upgrade_task
from onegov.search.utils import searchable_sqlalchemy_models


@upgrade_task('Adding full text search index column to postgres 42')
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
    # onegov-core upgrade

    session = context.session
    schema = context.schema

    for model in searchable_sqlalchemy_models(Base):
        if context.has_table(model.__tablename__):
            model.add_fts_column(session, schema, model)
