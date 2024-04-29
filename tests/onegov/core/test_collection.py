import pytest

from onegov.core.collection import GenericCollection, Pagination
from onegov.core.orm import SessionManager
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base


def test_pagination():

    class Query:

        def __init__(self, values):
            self.values = values
            self.start = None
            self.end = None

        def __iter__(self):
            if self.start is None or self.end is None:
                return iter(self.values)
            else:
                return iter(self.values[self.start:self.end])

        def slice(self, start, end):
            self.start = start
            self.end = end

            return self

        def count(self):
            return len(self.values)

        def order_by(self, *args):
            return self

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

    assert collection.batch == tuple(range(0, 10))
    assert collection.next.batch == tuple(range(10, 20))
    assert collection.next.next.batch == tuple(range(20, 25))
    assert collection.next.next.next is None

    assert collection.next.previous.batch == tuple(range(0, 10))
    assert collection.next.previous == collection

    pages = collection.pages
    assert next(pages).batch == tuple(range(0, 10))
    assert next(pages).batch == tuple(range(10, 20))
    assert next(pages).batch == tuple(range(20, 25))


def test_pagination_negative_page_index():
    class MyCollection(Pagination):

        def __init__(self, page, values=None):
            super().__init__(page)
            self.values = values

        @property
        def page_index(self):
            return self.page

        def page_by_index(self, index):
            return MyCollection(index, self.values)

    # test negative page index
    collection = MyCollection(page=-99)
    assert collection.page == 0
    assert collection.page_index == 0
    assert collection.page_by_index(-199).page == 0
    assert collection.page_by_index(-199).page_index == 0

    with pytest.raises(AssertionError):
        MyCollection(page=None)


def test_generic_collection(postgres_dsn):
    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'document'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    class DocumentCollection(GenericCollection):

        @property
        def model_class(self):
            return Document

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('generic_collection')

    collection = DocumentCollection(mgr.session())
    assert collection.query().all() == []

    readme = collection.add(title="Readme")
    assert [c.title for c in collection.query().all()] == ["Readme"]
    assert collection.by_id(readme.id).title == "Readme"

    collection.delete(readme)
    assert collection.query().all() == []
    assert collection.by_id(readme.id) is None
