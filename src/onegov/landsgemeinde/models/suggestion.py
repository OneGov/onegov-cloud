from __future__ import annotations

from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.people import Person
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from sqlalchemy.sql.elements import SQLCoreOperations


class Suggestion:

    """ Provide suggestions based on entries in the directory of persons and
    past vota.

    """

    def __init__(self, session: Session, term: str | None = '') -> None:
        self.session = session
        self.term = term
        self.limit = 5

    @property
    def votum_expression(
        self
    ) -> SQLCoreOperations[str | None]:
        raise NotImplementedError()

    @property
    def person_expressions(
        self
    ) -> tuple[SQLCoreOperations[str | None], ...]:
        raise NotImplementedError()

    def query(self) -> list[str]:
        result: list[str] = []

        if not self.term:
            return result

        for expression in self.person_expressions:
            query = self.session.query(expression)
            query = query.filter(
                expression.is_not(None),
                func.trim(expression) != '',
            )
            if self.term:
                query = query.filter(
                    expression.ilike(f'%{self.term}%')
                )
            query = query.order_by(expression)
            query = query.limit(self.limit)
            result.extend(r[0] for r in query)
        result = sorted(set(result))

        query = self.session.query(self.votum_expression)
        query = query.join(AgendaItem)
        query = query.join(Assembly)
        query = query.filter(
            self.votum_expression.is_not(None),
            func.trim(self.votum_expression) != '',
        )
        if self.term:
            query = query.filter(
                self.votum_expression.ilike(f'%{self.term}%')
            )
        query = query.order_by(
            Assembly.date.desc(),
            self.votum_expression
        )
        query = query.limit(self.limit)
        result.extend(
            x for x in dict.fromkeys(r[0] for r in query).keys()
            if x not in result
        )

        return result


class PersonNameSuggestion(Suggestion):

    @property
    def votum_expression(self) -> SQLCoreOperations[str | None]:
        return Votum.person_name

    @property
    def person_expressions(self) -> tuple[SQLCoreOperations[str]]:
        return (func.concat(Person.first_name, ' ', Person.last_name),)


class PersonFunctionSuggestion(Suggestion):

    @property
    def votum_expression(self) -> SQLCoreOperations[str | None]:
        return Votum.person_function

    @property
    def person_expressions(self) -> tuple[SQLCoreOperations[str | None], ...]:
        return (Person.function, Person.profession)


class PersonPlaceSuggestion(Suggestion):

    @property
    def votum_expression(self) -> SQLCoreOperations[str | None]:
        return Votum.person_place

    @property
    def person_expressions(self) -> tuple[SQLCoreOperations[str | None], ...]:
        return (Person.postal_code_city, Person.location_code_city)


class PersonPoliticalAffiliationSuggestion(Suggestion):

    @property
    def votum_expression(self) -> SQLCoreOperations[str | None]:
        return Votum.person_political_affiliation

    @property
    def person_expressions(self) -> tuple[SQLCoreOperations[str | None], ...]:
        return (Person.parliamentary_group, Person.political_party)
