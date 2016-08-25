from cached_property import cached_property
from elasticsearch_dsl.query import MultiMatch, MatchPhrase
from onegov.core.collection import Pagination


class Search(Pagination):

    results_per_page = 10
    max_query_length = 100

    def __init__(self, request, query, page):
        self.request = request
        self.query = query
        self.page = page

    @cached_property
    def available_documents(self):
        search = self.request.app.es_search_by_request(self.request)
        search = search.params(search_type="count")

        return search.execute().hits.total

    @cached_property
    def explain(self):
        return self.request.is_manager and 'explain' in self.request.params

    @property
    def q(self):
        return self.query

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
        search = self.request.app.es_search_by_request(
            request=self.request,
            explain=self.explain
        )

        # queries need to be cut at some point to make sure we're not
        # pushing the elasticsearch cluster to the brink
        query = self.query[:self.max_query_length]

        # make sure the title matches with a higher priority, otherwise the
        # "get lucky" functionality is not so lucky after all
        match_title = MatchPhrase(title={"query": query, "boost": 3})
        match_rest = MultiMatch(query=query, fields=[
            'title', 'lead', 'text', 'email', 'function', 'number',
            'ticket_email', 'ticket_data', 'description', 'location',
            'group'
        ], fuzziness='1')

        search = search.query(match_title | match_rest)
        search.query.minimum_should_match = 1
        search = search[self.offset:self.offset + self.batch_size]

        return search.execute()

    def feeling_lucky(self):
        if self.batch:
            first_entry = self.batch[0].load()

            # XXX the default view to the event should be doing the redirect
            if first_entry.__tablename__ == 'events':
                return self.request.link(first_entry, 'latest')
            else:
                return self.request.link(first_entry)

    @cached_property
    def subset_count(self):
        return self.cached_subset.hits.total

    def suggestions(self):
        return tuple(self.request.app.es_suggestions_by_request(
            self.request, self.query
        ))
