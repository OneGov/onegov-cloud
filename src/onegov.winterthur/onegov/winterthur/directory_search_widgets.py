from onegov.winterthur.app import WinterthurApp


@WinterthurApp.directory_search_widget('inline')
class InlineSearch(object):

    def __init__(self, app, directory, search_query):
        self.app = app
        self.directory = directory
        self.search_query = search_query

    def html(self, layout):
        return f'<b>{self.name}</b>'

    def adapt(self, query):
        return query
