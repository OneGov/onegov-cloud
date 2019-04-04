from cached_property import cached_property
from onegov.agency.models import ExtendedPerson
from onegov.core.collection import Pagination
from onegov.people import Agency
from onegov.people import AgencyMembership
from onegov.people import PersonCollection
from sqlalchemy import func
from sqlalchemy import or_


class ExtendedPersonCollection(PersonCollection, Pagination):
    """ Extends the common person collection by the ability to filter by
    the first letter of the last name and by the organization. Adds pagination.

    """

    batch_size = 20

    @property
    def model_class(self):
        return ExtendedPerson

    def __init__(self, session, page=0, letter=None, agency=None):
        self.session = session
        self.page = page
        self.letter = letter.upper() if letter else None
        self.agency = agency
        self.exclude_hidden = False

    def subset(self):
        return self.query()

    def __eq__(self, other):
        return (
            self.page == other.page
            and self.letter == other.letter
            and self.agency == other.agency
        )

    def page_by_index(self, page):
        return self.__class__(
            self.session,
            page=page,
            letter=self.letter,
            agency=self.agency
        )

    def for_filter(self, **kwargs):
        return self.__class__(
            session=self.session,
            letter=kwargs.get('letter', self.letter),
            agency=kwargs.get('agency', self.agency)
        )

    def query(self):
        query = self.session.query(ExtendedPerson)
        if self.exclude_hidden:
            query = query.filter(
                or_(
                    ExtendedPerson.meta['is_hidden_from_public'] == False,
                    ExtendedPerson.meta['is_hidden_from_public'] == None,
                )
            )
        if self.letter:
            query = query.filter(
                func.upper(
                    func.unaccent(ExtendedPerson.last_name)
                ).startswith(self.letter)
            )
        if self.agency:
            query = query.join(ExtendedPerson.memberships)
            query = query.join(AgencyMembership.agency)
            query = query.filter(Agency.title == self.agency)
        query = query.order_by(
            func.upper(func.unaccent(ExtendedPerson.last_name)),
            func.upper(func.unaccent(ExtendedPerson.first_name))
        )
        return query

    @cached_property
    def used_letters(self):
        """ Returns a list of all the distinct first letters of the peoples
        last names.

        """
        letter = func.left(ExtendedPerson.last_name, 1)
        letter = func.upper(func.unaccent(letter))
        query = self.session.query(letter.distinct().label('letter'))
        query = query.order_by(letter)
        return [r.letter for r in query]

    @cached_property
    def used_agencies(self):
        """ Returns a list of all the agencies peoples are members of.

        """
        query = self.session.query(Agency.title).distinct()
        query = query.join(Agency.memberships)
        query = query.order_by(func.upper(func.unaccent(Agency.title)))
        return [r.title for r in query]
