from __future__ import annotations

from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.sql import ColumnElement


# FIXME: Considering how simple this is when implemented correctly, we
#        should just get rid of this utility, unless we sometimes actually
#        pass in a boolean value, rather than a literal
def bool_is(
    column: ColumnElement[bool | None],
    value: bool
) -> ColumnElement[bool]:
    """ Returns a SqlAlchemyStatements checking for boolean values of JSON
    attibutes. Missing values are interpreted as False. """

    # FIXME: For some reason when using `is_` on JSONB data it will coerce
    #        both sides of the operation to a string, which is not what we
    #        want... This seems like a bug, maybe it's fixed upstream
    #        even | instead of or_ appears to be causing issues, so I think
    #        there is some aggressive coercion to str happening for JSONB
    #        when not using very specific things...
    if value:
        return column == True
    else:
        return or_(column != True, column == None)
