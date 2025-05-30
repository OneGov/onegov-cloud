""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<https://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.file import MultiAssociatedFiles


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from sqlalchemy import Column
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import ColumnElement


class Page(AdjacencyList, ContentMixin, TimestampMixin,
           UTCPublicationMixin, MultiAssociatedFiles):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    if TYPE_CHECKING:
        # we override these relationships to be more specific
        parent: relationship[Page | None]
        children: relationship[list[Page]]

        @property
        def root(self) -> Page: ...
        @property
        def ancestors(self) -> Iterator[Page]: ...

        # HACK: Workaround for hybrid_property not working until SQLAlchemy 2.0
        published_or_created: Column[datetime]
    else:
        @hybrid_property
        def published_or_created(self) -> datetime:
            return self.publication_start or self.created

        @published_or_created.expression  # type:ignore[no-redef]
        def published_or_created(cls) -> ColumnElement[datetime]:
            return func.coalesce(Page.publication_start, Page.created)
