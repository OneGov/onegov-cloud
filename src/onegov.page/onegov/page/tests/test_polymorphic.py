import pytest
from onegov.page import Page, PageCollection


class Article(Page):
    __mapper_args__ = {'polymorphic_identity': 'article'}


def test_article(session):
    pages = PageCollection(session)
    root = pages.add_root("Root")

    page = pages.add(parent=root, title='Article', type='article')
    assert isinstance(page, Article)

    page = pages.add(parent=root, title='Page')
    assert not isinstance(page, Article)

    page = pages.add(parent=root, title='Test', type='generic')
    assert not isinstance(page, Article)

    assert isinstance(pages.by_path('/root/article'), Article)
    assert not isinstance(pages.by_path('/root/page'), Article)

    with pytest.raises(AssertionError) as assertion_info:
        assert not isinstance(pages.by_path('/root/test'), Article)

    assert "No such polymorphic_identity" in str(assertion_info.value)

    assert pages.by_path('/root/article')
    assert pages.by_path('/root/article', ensure_type='article')
    assert not pages.by_path('/root/article', ensure_type='missing')
    assert not pages.by_path('/root/inexistant', ensure_type='article')
