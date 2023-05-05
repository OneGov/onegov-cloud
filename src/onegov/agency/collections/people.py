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
    the first letter of the last name, by the organization, by first or last
    name. Adds pagination.

    """

    batch_size = 20

    @property
    def model_class(self):
        return ExtendedPerson

    def __init__(self, session, page=0, letter=None, agency=None,
                 first_name=None, last_name=None,
                 xlsx_modified=None):
        self.session = session
        self.page = page

        # filter keywords
        self.letter = letter.upper() if letter else None
        self.agency = agency
        self.first_name = first_name
        self.last_name = last_name
        # end filter keywords

        self.exclude_hidden = False
        # Usage for link generation of people excel based on timestamp
        self.xlsx_modified = xlsx_modified

    def subset(self):
        return self.query()

    def __eq__(self, other):
        return (
            self.page == other.page
            and self.letter == other.letter
            and self.agency == other.agency
            and self.first_name == other.first_name
            and self.last_name == other.last_name
        )

    def page_by_index(self, page):
        return self.__class__(
            self.session,
            page=page,
            letter=self.letter,
            agency=self.agency,
            first_name=self.first_name,
            last_name=self.last_name,
        )

    def for_filter(self, **kwargs):
        return self.__class__(
            session=self.session,
            letter=kwargs.get('letter', self.letter),
            agency=kwargs.get('agency', self.agency),
            first_name=kwargs.get('first_name', self.first_name),
            last_name=kwargs.get('last_name', self.last_name),
        )

    def query(self):
        query = self.session.query(ExtendedPerson)
        if self.exclude_hidden:
            query = query.filter(
                or_(
                    ExtendedPerson.meta['access'] == 'public',
                    ExtendedPerson.meta['access'] == None,
                ),
                ExtendedPerson.published.is_(True)
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
        if self.first_name:
            query = query.filter(
                func.lower(
                    func.unaccent(ExtendedPerson.first_name)

                ) == self.first_name.lower()
            )
        if self.last_name:
            query = query.filter(
                func.lower(
                    func.unaccent(ExtendedPerson.last_name)

                ) == self.last_name.lower()
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
