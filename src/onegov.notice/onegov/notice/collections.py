from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.notice.models import OfficialNotice
from sqlalchemy import or_


class OfficialNoticeCollectionPagination(Pagination):

    def __init__(self, session, page=0, state=None, term=None):
        self.session = session
        self.page = page
        self.state = state
        self.term = term

    def __eq__(self, other):
        return (
            self.state == other.state and
            self.page == other.page and
            self.term == other.term
        )

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.state, self.term)

    def for_state(self, state):
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(self.session, 0, state, self.term)


class OfficialNoticeCollection(OfficialNoticeCollectionPagination):
    """ Manage a list of official notices. """

    @property
    def model_class(self):
        return OfficialNotice

    def query(self):
        query = self.session.query(self.model_class)
        if self.state:
            query = query.filter(self.model_class.state == self.state)
        if self.term:
            term = '%{}%'.format(self.term)
            query = query.filter(
                or_(
                    self.model_class.title.ilike(term),
                    self.model_class.text.ilike(term)
                )
            )
        return query

    def _get_unique_name(self, name):
        """ Create a unique, URL-friendly name. """

        # it's possible for `normalize_for_url` to return an empty string...
        name = normalize_for_url(name) or "notice"

        session = self.session
        while session.query(self.model_class.name).\
                filter(self.model_class.name == name).first():
            name = increment_name(name)

        return name

    def add(self, title, text, **optional):
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        Returns the created notice.
        """
        notice = self.model_class(
            state='drafted',
            name=self._get_unique_name(title),
            title=title,
            text=text,
            **optional
        )

        self.session.add(notice)
        self.session.flush()

        return notice

    def delete(self, notice):
        """ Delete an notice. """

        self.session.delete(notice)
        self.session.flush()

    def by_name(self, name):
        """ Returns a notice by its URL-friendly name. """

        query = self.session.query(self.model_class)
        query = query.filter(self.model_class.name == name)
        return query.first()

    def by_id(self, id):
        """ Returns a notice by its id. """

        query = self.session.query(self.model_class)
        query = query.filter(self.model_class.id == id)
        return query.first()
