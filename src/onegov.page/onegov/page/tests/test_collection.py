import pytest
from onegov.page import PageCollection


def test_add_page(session):

    pages = PageCollection(session)
    root = pages.add_root(title='Test')

    assert root.name == 'test'
    assert root.title == 'Test'
    assert root.root is root
    assert list(root.ancestors) == []
    assert root.path == 'test'
    assert root.absorb == 'test'
    assert root.type is None

    child = pages.add(parent=root, title='Foo Bar')

    assert child.name == 'foo-bar'
    assert child.title == 'Foo Bar'
    assert child.root is root
    assert list(child.ancestors) == [root]
    assert child.path == 'test/foo-bar'
    assert child.absorb == 'test/foo-bar'

    with pytest.raises(AssertionError):
        # normalized names are enforced
        child.name = 'Bar Foo'

    grandchild = pages.add(parent=child, title='Grandchild')
    assert list(grandchild.ancestors) == [root, child]
    assert repr(grandchild) == "Page(name='grandchild', id=3, parent_id=2)"


def test_add_unique_page(session):

    pages = PageCollection(session)
    r1 = pages.add_root(title='Test')
    r2 = pages.add_root(title='Test')
    r3 = pages.add_root(title='Test')

    assert r1.name == 'test'
    assert r2.name == 'test-1'
    assert r3.name == 'test-2'

    c1 = pages.add(parent=r1, title='Test')
    c2 = pages.add(parent=r1, title='Test')
    c3 = pages.add(parent=r1, title='Test')

    assert c1.name == 'test'
    assert c2.name == 'test-1'
    assert c3.name == 'test-2'


def test_move_page(session):

    pages = PageCollection(session)
    root = pages.add_root(title='Root')

    c1 = pages.add(parent=root, title='One')
    c2 = pages.add(parent=root, title='Two')

    pages.move(c1, new_parent=c2)

    assert c1.parent is c2
    assert c2.parent is root


def test_add_or_get_page(session):

    pages = PageCollection(session)
    root = pages.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'

    root = pages.add_or_get_root(title='Wurzel', name='root')

    assert root.title == 'Wurzel'
    assert root.name == 'root'


def test_copy_page(session):

    pages = PageCollection(session)
    news = pages.add_root('News')

    new_page = pages.add(parent=news, title='New Homepage')
    assert [p.name for p in news.children] == ['new-homepage']

    pages.copy(new_page, news)
    assert [p.name for p in news.children] == [
        'new-homepage', 'new-homepage-1'
    ]


def test_page_by_path(session):

    pages = PageCollection(session)

    news = pages.add_root('News')
    assert pages.by_path('/news') is news
    assert pages.by_path('/news/') is news
    assert pages.by_path('news/') is news
    assert pages.by_path('news') is news
    assert pages.by_path('/neues') is None

    toast = pages.add(parent=news, title='Yeah Toast')
    assert pages.by_path('/news/yeah-toast') is toast
    assert pages.by_path('news/yeah-toast') is toast
    assert pages.by_path('news/yeah-toast/') is toast
    assert pages.by_path('/news/yeah-toast/') is toast
    assert pages.by_path('/news/jah-toast') is None


def test_delete(session):
    pages = PageCollection(session)

    news = pages.add_root('News')
    assert pages.by_path('/news') is news

    pages.delete(news)

    assert pages.by_path('/news') is None
