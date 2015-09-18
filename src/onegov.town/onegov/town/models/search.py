from cached_property import cached_property
from onegov.core.collection import Pagination


class Search(Pagination):

    results_per_page = 10

    def __init__(self, request, query, page):
        self.request = request
        self.query = query
        self.page = page

    def __eq__(self, other):
        return self.page == other.page and self.query == other.query

    def subset(self):
        return self.batch

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return Search(self.request, self.query, index)

    @cached_property
    def batch(self):
        search = self.request.app.es_search_by_request(self.request)
        search = search.query('multi_match', query=self.query, fields=[
            'title', 'lead', 'text'
        ], fuzziness='AUTO', analyzer='german')
        search = search[self.offset:self.offset + self.batch_size]

        return search.execute()

    @cached_property
    def subset_count(self):
        return self.cached_subset.hits.total
