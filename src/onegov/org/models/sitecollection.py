from __future__ import annotations

from onegov.form.models import FormDefinition
from onegov.reservation import Resource
from onegov.directory import Directory
from onegov.org.models.file import ImageSet
from onegov.org.models.page import News, Topic
from sqlalchemy.orm import defer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session


class SiteCollection:

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def get_topics(session: Session) -> Query[Topic]:
        topics = session.query(Topic)
        topics = topics.options(defer(Topic.meta))
        topics = topics.options(defer(Topic.content))
        topics = topics.options(defer(Topic.order))
        topics = topics.order_by(Topic.title)
        return topics

    @staticmethod
    def get_news(session: Session) -> Query[News]:
        news = session.query(News)
        news = news.options(defer(News.meta))
        news = news.options(defer(News.content))
        news = news.options(defer(News.order))
        news = news.order_by(News.title)
        return news

    @staticmethod
    def get_forms(session: Session) -> Query[FormDefinition]:
        forms = session.query(FormDefinition)
        forms = forms.options(defer(FormDefinition.definition))
        forms = forms.options(defer(FormDefinition.checksum))
        forms = forms.order_by(FormDefinition.title)
        return forms

    @staticmethod
    def get_resources(session: Session) -> Query[Resource]:
        resources = session.query(Resource)
        resources = resources.options(defer(Resource.timezone))
        resources = resources.order_by(Resource.title)
        return resources

    @staticmethod
    def get_directories(session: Session) -> Query[Directory]:
        directories = session.query(Directory)
        directories = directories.options(defer(Directory.meta))
        directories = directories.options(defer(Directory.content))
        directories = directories.options(defer(Directory.lead))
        directories = directories.options(defer(Directory.structure))
        directories = directories.options(defer(Directory.configuration))
        directories = directories.order_by(Directory.order)
        return directories

    @staticmethod
    def get_imagesets(session: Session) -> Query[ImageSet]:
        imagesets = session.query(ImageSet)
        imagesets = imagesets.options(defer(ImageSet.meta))
        imagesets = imagesets.options(defer(ImageSet.content))
        imagesets = imagesets.order_by(ImageSet.title)
        return imagesets

    def get(self) -> dict[str, tuple[Any, ...]]:
        return {
            'topics': tuple(self.get_topics(self.session)),
            'news': tuple(self.get_news(self.session)),
            'forms': tuple(self.get_forms(self.session)),
            'resources': tuple(self.get_resources(self.session)),
            'directories': tuple(self.get_directories(self.session)),
            'imagesets': tuple(self.get_imagesets(self.session)),
        }
