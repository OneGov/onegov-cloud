from sqlalchemy import or_


def bool_is(column, value):
    """ Returns a SqlAlchemyStatements checking for boolean values of JSON
    attibutes. Missing values are interpreted as False. """

    return column == True if value else or_(column != True, column == None)
    if value:
        return column == True
    else:
        return or_(column != True, column == None)
