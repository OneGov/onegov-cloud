from cached_property import cached_property
from collections import OrderedDict
from itertools import groupby
from unidecode import unidecode


class AtoZ(object):

    def __init__(self, request):
        self.request = request

    def sortkey(self, page):
        return unidecode(page.title[0].upper())

    @cached_property
    def pages(self):
        from onegov.town.models.page import Topic

        # XXX implement correct collation support on the database level
        topics = self.request.app.session().query(Topic).all()
        topics = sorted(topics, key=self.sortkey)

        if self.request.is_logged_in:
            return [topic for topic in topics if topic.trait == 'page']
        else:
            return [
                topic for topic in topics if topic.trait == 'page'
                and not topic.is_hidden_from_public
            ]

    def pages_by_letter(self):
        pages_by_letter = OrderedDict()

        for letter, pages in groupby(self.pages, self.sortkey):
            # sort the pages again, because for the grouping we only use the
            # first letter
            pages_by_letter[unidecode(letter)] = tuple(
                sorted(pages, key=lambda p: unidecode(p.title))
            )

        return pages_by_letter
