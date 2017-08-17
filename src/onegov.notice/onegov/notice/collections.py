from onegov.core.collection import Pagination
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
from onegov.notice.models import OfficialNotice
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import inspect
from sqlalchemy import or_


class OfficialNoticeCollectionPagination(Pagination):

    def __init__(
        self,
        session,
        page=0,
        state=None,
        term=None,
        order=None,
        direction=None,
        issues=None,
        user_ids=None
    ):
        self.session = session
        self.page = page
        self.state = state
        self.term = term
        self.user_ids = user_ids or []
        self.order = order or 'title'
        self.direction = direction or 'asc'
        self.issues = issues

    def __eq__(self, other):
        return (
            self.state == other.state and
            self.page == other.page and
            self.term == other.term and
            self.order == other.order and
            self.direction == other.direction and
            self.issues == other.issues
        )

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(
            self.session,
            page=index,
            state=self.state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues
        )

    def for_state(self, state):
        """ Returns a new instance of the collection with the given state. """

        return self.__class__(
            self.session,
            state=state,
            term=self.term,
            order=self.order,
            direction=self.direction,
            issues=self.issues
        )

    def for_order(self, order, direction=None):
        """ Returns a new instance of the collection with the given ordering.
        Inverts the direction if the new ordering is the same as the old one
        and an explicit ordering is not defined.

        """
        if direction is not None:
            descending = direction == 'desc'
        elif self.order != order:
            descending = False
        else:
            descending = self.direction != 'desc'

        return self.__class__(
            self.session,
            state=self.state,
            term=self.term,
            order=order,
            direction='desc' if descending else 'asc',
            issues=self.issues
        )


class OfficialNoticeCollection(OfficialNoticeCollectionPagination):
    """ Manage a list of official notices. """

    @property
    def model_class(self):
        return OfficialNotice

    def query(self):
        """ Returns a query with the given state and users filter applied and
        sorted by the given column / direction.

        """
        query = self.session.query(self.model_class)

        # filtering
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
        if self.user_ids:
            query = query.filter(self.model_class.user_id.in_(self.user_ids))
        if self.issues:
            query = query.filter(self.model_class._issues.has_any(self.issues))

        direction = desc if self.direction == 'desc' else asc
        if self.order in inspect(self.model_class).columns.keys():
            attribute = getattr(self.model_class, self.order)
        else:
            attribute = self.model_class.title
        query = query.order_by(None).order_by(direction(attribute))

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
        issues = optional.pop('issues', None)
        notice = self.model_class(
            state='drafted',
            name=self._get_unique_name(title),
            title=title,
            text=text,
            **optional
        )
        if issues:
            notice.issues = issues

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
