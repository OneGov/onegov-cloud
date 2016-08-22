from onegov.core.orm.abstract import MoveDirection
from onegov.core.utils import Bunch
from onegov.page import PageCollection


class AdjacencyListMove(object):
    """ Represents a single move of an adjacency list item. """

    def __init__(self, session, subject, target, direction):
        self.session = session
        self.subject = subject
        self.target = target
        self.direction = direction

    @classmethod
    def for_url_template(cls):
        return cls(
            session=None,
            subject=Bunch(id='{subject_id}'),
            target=Bunch(id='{target_id}'),
            direction='{direction}'
        )

    @property
    def subject_id(self):
        return self.subject.id

    @property
    def target_id(self):
        return self.target.id

    def execute(self):
        self.__collection__(self.session).move(
            subject=self.subject,
            target=self.target,
            direction=getattr(MoveDirection, self.direction)
        )


class PageMove(AdjacencyListMove):
    __collection__ = PageCollection
