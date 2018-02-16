import os
import psqlparse
import re

from onegov.core.orm import types as onegov_types
from sqlalchemy import text
from sqlalchemy import types as sqlalchemy_types
from uuid import uuid4


NESTED_TYPE = re.compile(r'(\w+)\((\w+)\)')


def as_selectable(query, alias=None):
    """ Takes a raw SQL query and turns it into a selectable SQLAlchemy
    expression using annotations in comments.

    Expects to find a SELECT statement like this::

        SELECT
            foo,  -- Text
            bar   -- Integer
        FROM
            foobar

    The so created selectable can be used by SQLAlchemy::

        from sqlalchemy import select

        query = as_selectable('''
            SELECT
                foo, -- Text
                bar  -- Integer
            FROM
                foobar
        ''')

        session.execute(select(query.c).where(query.c.foo == 'bar'))

    """

    # use the last statement if there are many
    statement = psqlparse.parse(query)[-1]

    # find the columns and use the comment to load types
    columns = {
        column: type_by_string(comment)
        for column, comment
        in column_names_with_comments(statement, query)
    }

    # an alias is required to reuse this query later
    alias = alias or ('q-' + uuid4().hex[:10])

    # turn the query into a selectable
    return text(query).columns(**columns).alias(alias)


def type_by_string(expression):
    nested = NESTED_TYPE.match(expression)

    if nested:
        name, nested = nested.groups()
        return type_by_string(name)(type_by_string(nested))

    return getattr(onegov_types, expression, None) \
        or getattr(sqlalchemy_types, expression)


def as_selectable_from_path(path):
    alias = os.path.basename(path).split('.', 1)[0]

    with open(path, 'r') as f:
        return as_selectable(f.read(), alias=alias)


def column_names_with_comments(statement, query):
    for target in statement.target_list.targets:

        # expression
        if 'name' in target:
            column = target['name']

        # ordinary column
        elif 'val' in target and 'ColumnRef' in target['val']:
            column = target['val']['ColumnRef']['fields'][-1]['String']['str']

        else:
            raise NotImplementedError

        # find the next inline-comment
        location = target['location']

        at = query.find('--', location) + 2
        to = query.find('\n', at)

        assert at and to

        yield column, query[at:to].strip()
