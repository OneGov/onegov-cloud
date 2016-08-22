from onegov.form.models import FormDefinition
from onegov.libres.models import Resource
from onegov.org.models.file import ImageSet
from onegov.org.models.page import News, Topic
from sqlalchemy.orm import defer


class SiteCollection(object):

    def __init__(self, session):
        self.session = session

    def get(self):
        # get the topics
        topics = self.session.query(Topic)
        topics = topics.options(defer(Topic.meta))
        topics = topics.options(defer(Topic.content))
        topics = topics.options(defer(Topic.order))
        topics = topics.order_by(Topic.title)

        # get the news
        news = self.session.query(News)
        news = news.options(defer(News.meta))
        news = news.options(defer(News.content))
        news = news.options(defer(News.order))
        news = news.order_by(News.title)

        # get the forms
        forms = self.session.query(FormDefinition)
        forms = forms.options(defer(FormDefinition.definition))
        forms = forms.options(defer(FormDefinition.checksum))
        forms = forms.order_by(FormDefinition.title)

        # get the resources
        resources = self.session.query(Resource)
        resources = resources.options(defer(Resource.timezone))
        resources = resources.order_by(Resource.title)

        # get the foto albums
        imagesets = self.session.query(ImageSet)
        imagesets = imagesets.options(defer(ImageSet.meta))
        imagesets = imagesets.options(defer(ImageSet.content))
        imagesets = imagesets.order_by(ImageSet.title)

        return {
            'topics': topics.all(),
            'news': news.all(),
            'forms': forms.all(),
            'resources': resources.all(),
            'imagesets': imagesets.all(),
        }
