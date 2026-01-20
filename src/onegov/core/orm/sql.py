from __future__ import annotations

import os
import pglast  # type:ignore[import-untyped]
import re

from functools import lru_cache
from onegov.core.orm import types as onegov_types
from sqlalchemy import text
from sqlalchemy import types as sqlalchemy_types
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pglast.ast import RawStmt  # type:ignore[import-untyped]
    from sqlalchemy.sql.selectable import Alias
    from sqlalchemy.types import TypeEngine


NESTED_TYPE = re.compile(r'(\w+)\((\w+)\)')


def as_selectable(query: str, alias: str | None = None) -> Alias:
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
    statement = pglast.parse_sql(query)[-1]

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


def type_by_string(
    expression: str
) -> type[TypeEngine[Any]] | TypeEngine[Any]:
    nested_match = NESTED_TYPE.match(expression)

    if nested_match:
        name, nested = nested_match.groups()
        return type_by_string(name)(type_by_string(nested))  # type:ignore

    return (
        getattr(onegov_types, expression, None)
        or getattr(sqlalchemy_types, expression)
    )


@lru_cache(maxsize=64)
def as_selectable_from_path(path: str) -> Alias:
    alias = os.path.basename(path).split('.', 1)[0]

    with open(path) as f:
        return as_selectable(f.read(), alias=alias)


def column_names_with_comments(
    statement: RawStmt,
    query: str
) -> Iterator[tuple[str, str]]:

    for target in statement.stmt.targetList:

        # expression
        if target.name:
            column = target.name

        # ordinary column
        elif isinstance(target.val, pglast.ast.ColumnRef):
            string = target.val.fields[-1]
            assert isinstance(string, pglast.ast.String)
            column = string.sval
        else:
            raise NotImplementedError

        # find the next inline-comment
        location = target.location

        at = query.find('--', location) + 2
        to = query.find('\n', at)

        assert at and to

        yield column, query[at:to].strip()
