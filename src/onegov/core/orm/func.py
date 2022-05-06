from sqlalchemy.sql.functions import ReturnTypeFromArgs


class unaccent(ReturnTypeFromArgs):
    """ Produce a UNACCENT expression. """

    inherit_cache = True
