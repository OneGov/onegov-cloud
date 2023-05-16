import operator

from sqlalchemy import func


def filter_modified_or_created(query, relate, comparison_property,
                               collection_class):
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
    }
    assert relate in ops.keys()

    return query.filter(
        ops[relate](
            # if 'modified' is not set comparison is done against 'created'
            func.coalesce(
                func.date_trunc('minute',
                                collection_class.modified),
                func.date_trunc('minute',
                                collection_class.created),
            ),
            comparison_property
        )
    )
