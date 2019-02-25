
def get_table_column(table, name):
    """ Returns the column with the given name.

    Expects the given column to be either a SqlAlchemy column or an
    encoded_property, and the column name to be optionally prefixed with an
    underline.

    """
    try:
        return table.__table__.columns[name.lstrip('_')]
    except KeyError:
        return table.__class__.__dict__[name.lstrip('_')]
