from onegov.core.collection import Pagination


def test_pagination():

    class Query(object):

        def __init__(self, values):
            self.values = values
            self.start = None
            self.end = None

        def all(self):
            if self.start is None or self.end is None:
                return self.values
            else:
                return self.values[self.start:self.end]

        def slice(self, start, end):
            self.start = start
            self.end = end

            return self

        def count(self):
            return len(self.all())

    class Collection(Pagination):

        def __init__(self, page, values):
            self.page = page
            self.values = values

        @property
        def page_index(self):
            return self.page

        def __eq__(self, other):
            return self.page_index == other.page_index

        def subset(self):
            return Query(self.values)

        def page_by_index(self, index):
            return Collection(index, self.values)

    collection = Collection(page=0, values=list(range(0, 25)))

    assert collection.subset_count == 25
    assert collection.offset == 0
    assert collection.previous is None
    assert collection.next is not None

    assert collection.batch == list(range(0, 10))
    assert collection.next.batch == list(range(10, 20))
    assert collection.next.next.batch == list(range(20, 25))
    assert collection.next.next.next is None

    assert collection.next.previous.batch == list(range(0, 10))
    assert collection.next.previous == collection

    pages = collection.pages
    assert next(pages).batch == list(range(0, 10))
    assert next(pages).batch == list(range(10, 20))
    assert next(pages).batch == list(range(20, 25))
