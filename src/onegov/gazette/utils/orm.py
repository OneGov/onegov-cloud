from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.sql import ColumnElement


# FIXME: Considering how simple this is when implemented correctly, we
#        should just get rid of this utility, unless we sometimes actually
#        pass in a boolean value, rather than a literal
def bool_is(
    column: 'ColumnElement[bool | None]',
    value: bool
) -> 'ColumnElement[bool]':
    """ Returns a SqlAlchemyStatements checking for boolean values of JSON
    attibutes. Missing values are interpreted as False. """

    if value:
        return column.is_(True)
    else:
        return column.is_distinct_from(True)
