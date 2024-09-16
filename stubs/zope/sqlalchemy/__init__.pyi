from zope.sqlalchemy.datamanager import (
    ZopeTransactionEvents as ZopeTransactionEvents,
    mark_changed as mark_changed,
    register as register,
)

invalidate = mark_changed
