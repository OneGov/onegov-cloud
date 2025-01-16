from __future__ import annotations

from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.election_day.models.file import File
from onegov.file import NamedFile
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from onegov.core.orm import SessionManager
    from onegov.election_day.types import DomainOfInfluence
    from onegov.election_day.types import Status
    from sqlalchemy.orm import Session
    from sqlalchemy.sql import ColumnElement


class DomainOfInfluenceMixin:
    """ Defines the scope of a principal, an election, an election compound
    or a vote.

    The following domains of influence are supported:
    - federation: The vote or election is nation wide.
    - canton: The vote or election takes place in one canton only.
    - region: The election takes place in one region of a canton only.
    - district: The election takes place in one district of a canton only.
    - municipality: The vote or election takes place in one municipality only.
    - none: The election takes place in certain municipalities only.

    """

    if TYPE_CHECKING:
        domain: Column[DomainOfInfluence]

    #: scope of the election or vote
    @declared_attr  # type:ignore[no-redef]
    def domain(cls) -> Column[DomainOfInfluence]:
        return Column(
            Enum(  # type:ignore[arg-type]
                'federation',
                'canton',
                'region',
                'district',
                'municipality',
                'none',
                name='domain_of_influence'
            ),
            nullable=False
        )


class StatusMixin:
    """ Mixin providing status indication for votes and elections. """

    if TYPE_CHECKING:
        status: Column[Status | None]

        # forward declare required attributes
        counted: Column[bool]

        @property
        def progress(self) -> tuple[int, int]: ...

    #: Status of the election or vote
    @declared_attr  # type:ignore[no-redef]
    def status(cls) -> Column[Status | None]:
        return Column(
            Enum(  # type:ignore[arg-type]
                'unknown',
                'interim',
                'final',
                name='election_or_vote_status'
            ),
            nullable=True
        )

    @property
    def completed(self) -> bool:
        """ Returns True, if the election or vote is completed.

        The status is evaluated in the first place. If the status is not known,
        it is guessed from the progress / counted fields.

        """

        if self.status == 'final':
            return True
        if self.status == 'interim':
            return False

        if self.progress[1] == 0:
            return False

        return self.counted


class TitleTranslationsMixin:
    """ Adds a helper to return the translation of the title without depending
    on the locale of the request.

    """

    if TYPE_CHECKING:
        # forward declare required attributes
        title_translations: (
            Column[Mapping[str, str]]
            | Column[Mapping[str, str] | None]
        )

    def get_title(
        self,
        locale: str,
        default_locale: str | None = None
    ) -> str | None:
        """ Returns the requested translation of the title, falls back to the
        given default locale if provided.

        """
        translations = self.title_translations or {}
        if default_locale is None:
            return translations.get(locale, None)
        return (
            translations.get(locale, None)
            or translations.get(default_locale, None)
        )


class IdFromTitlesMixin:

    if TYPE_CHECKING:
        # forward declare required attributes
        @property
        def session_manager(self) -> SessionManager | None: ...

        title_translations: (
            Column[Mapping[str, str]]
            | Column[Mapping[str, str] | None]
        )
        short_title_translations: Column[Mapping[str, str] | None]

        def get_title(
            self,
            locale: str,
            default_locale: str | None = None
        ) -> str | None: ...

    @property
    def polymorphic_base(self) -> type[Any]:
        raise NotImplementedError()

    def get_short_title(
        self,
        locale: str,
        default_locale: str | None = None
    ) -> str | None:
        """ Returns the requested translation of the short title, falls back
        to the full title.

        """
        translations = self.short_title_translations or {}
        return (
            translations.get(locale, None)
            or self.get_title(locale, default_locale)
        )

    def id_from_title(self, session: Session) -> str:
        """ Returns a unique, user friendly id derived from the title. """

        session_manager = self.session_manager
        assert session_manager is not None
        assert session_manager.default_locale
        locale = session_manager.default_locale
        title = self.get_short_title(locale)
        id = normalize_for_url(title or self.__class__.__name__)
        while True:
            query = session.query(self.polymorphic_base).filter_by(id=id)
            items = [item for item in query if item != self]
            if not items:
                return id
            id = increment_name(id)


def summarized_property(name: str) -> Column[int]:
    """ Adds an attribute as hybrid_property which returns the sum of the
    underlying results if called.

    Requires the class to define two aggregation functions.

    Usage::

        class Model():
            votes = summarized_property('votes')

            results = relationship('Result', ...)

            def aggregate_results(self, attribute):
                return sum(getattr(res, attribute) for res in self.results)

            @classmethod
            def aggregate_results_expression(cls, attribute):
                expr = select([func.sum(getattr(Result, attribute))])
                expr = expr.where(Result.xxx_id == cls.id)
                expr = expr.label(attribute)
                return expr

    """

    def getter(self: Any) -> int:
        return self.aggregate_results(name)

    def expression(cls: type[Any]) -> ColumnElement[int]:
        return cls.aggregate_results_expression(name)

    return hybrid_property(getter, expr=expression)  # type:ignore


class LastModifiedMixin(TimestampMixin):

    if TYPE_CHECKING:
        last_result_change: Column[datetime | None]
        last_modified: Column[datetime | None]

    @declared_attr  # type:ignore[no-redef]
    def last_result_change(cls) -> Column[datetime | None]:
        return Column(UTCDateTime)

    @hybrid_property  # type:ignore[no-redef]
    def last_modified(self) -> datetime | None:
        changes = [self.last_change, self.last_result_change]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @last_modified.expression  # type:ignore[no-redef]
    def last_modified(cls) -> ColumnElement[datetime | None]:
        return func.greatest(cls.last_change, cls.last_result_change)


class ExplanationsPdfMixin:

    files = associated(File, 'files', 'one-to-many', onupdate='CASCADE')

    explanations_pdf = NamedFile()
