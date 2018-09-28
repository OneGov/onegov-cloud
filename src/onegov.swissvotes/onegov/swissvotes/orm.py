from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FromClause


class values(FromClause):
    """ Productes a Postgres `VALUES` construct.

    Example:
        # FROM (VALUES ((1, 20), (2, 10))) AS lookup (id, count)
        # ORDER BY lookup.count
        query(
            values(
                [column('id', Integer), column('count', Integer)],
                [(1, 20), (2, 10)],
                alias_name='lookup'
            )
        ).order_by('lookup.count')

    Source: https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/PGValues

    """
    named_with_column = True

    def __init__(self, columns, *args, **kw):
        self._column_args = columns
        self.list = args
        self.alias_name = self.name = kw.pop('alias_name', None)

    def _populate_column_collection(self):
        for c in self._column_args:
            c._make_proxy(self)


@compiles(values)
def compile_values(element, compiler, asfrom=False, **kw):
    columns = element.columns
    v = "VALUES {}".format(
        ", ".join(
            "({})".format(
                ", ".join(
                    compiler.render_literal_value(elem, column.type)
                    for elem, column in zip(tup, columns)
                )
            )
            for tup in element.list
        )
    )
    if asfrom:
        if element.alias_name:
            v = "({}) AS {} ({})".format(
                v,
                element.alias_name,
                (", ".join(c.name for c in element.columns))
            )
        else:
            v = f"({v})"
    return v
