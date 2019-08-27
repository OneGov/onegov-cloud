from sqlalchemy.dialects.postgresql import HSTORE as HSTOREBase
from sqlalchemy.ext.mutable import MutableDict


class HSTORE(HSTOREBase):
    """ Extends the default HSTORE type to make it mutable by default. """


MutableDict.associate_with(HSTORE)
