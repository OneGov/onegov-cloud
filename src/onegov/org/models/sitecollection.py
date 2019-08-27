from onegov.form.models import FormDefinition
from onegov.reservation import Resource
from onegov.directory import Directory
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

        # get the directories
        directories = self.session.query(Directory)
        directories = directories.options(defer(Directory.meta))
        directories = directories.options(defer(Directory.content))
        directories = directories.options(defer(Directory.lead))
        directories = directories.options(defer(Directory.structure))
        directories = directories.options(defer(Directory.configuration))
        directories = directories.order_by(Directory.order)

        # get the foto albums
        imagesets = self.session.query(ImageSet)
        imagesets = imagesets.options(defer(ImageSet.meta))
        imagesets = imagesets.options(defer(ImageSet.content))
        imagesets = imagesets.order_by(ImageSet.title)

        return {
            'topics': tuple(topics),
            'news': tuple(news),
            'forms': tuple(forms),
            'resources': tuple(resources),
            'directories': tuple(directories),
            'imagesets': tuple(imagesets),
        }
