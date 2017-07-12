from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.notice.models import OfficialNotice


class OfficialNoticeCollectionPagination(Pagination):

    def __init__(self, session, page=0, state=None):
        self.session = session
        self.page = page
        self.state = state

    def __eq__(self, other):
        return self.state == other.state and self.page == other.page

    def subset(self):
        query = self.query()
        return query

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, index, self.state)

    def for_state(self, state):
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(self.session, 0, state)


class OfficialNoticeCollection(OfficialNoticeCollectionPagination):
    """ Manage a list of official notices. """

    def query(self):
        query = self.session.query(OfficialNotice)
        if self.state:
            query = query.filter(OfficialNotice.state == self.state)
        return query

    def _get_unique_name(self, name):
        """ Create a unique, URL-friendly name. """

        # it's possible for `normalize_for_url` to return an empty string...
        name = normalize_for_url(name) or "notice"

        session = self.session
        while session.query(OfficialNotice.name).\
                filter(OfficialNotice.name == name).first():
            name = increment_name(name)

        return name

    def add(self, title, text, **optional):
        """ Add a new notice.

        A unique, URL-friendly name is created automatically for this notice
        using the title and optionally numbers for duplicate names.

        Returns the created notice.
        """
        notice = OfficialNotice(
            state='drafted',
            title=title,
            name=self._get_unique_name(title),
            **optional
        )
        notice.content = {'text': text}

        self.session.add(notice)
        self.session.flush()

        return notice

    def delete(self, notice):
        """ Delete an notice. """

        self.session.delete(notice)
        self.session.flush()

    def by_name(self, name):
        """ Returns a notice by its URL-friendly name. """

        query = self.session.query(OfficialNotice)
        query = query.filter(OfficialNotice.name == name)
        return query.first()

    def by_id(self, id):
        """ Return a notice by its id. """

        query = self.session.query(OfficialNotice)
        query = query.filter(OfficialNotice.id == id)
        return query.first()
