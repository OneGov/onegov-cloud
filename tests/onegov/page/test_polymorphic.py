from __future__ import annotations

import pytest
from onegov.page import Page, PageCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class Article(Page):
    __mapper_args__ = {'polymorphic_identity': 'article'}


def test_article(session: Session) -> None:
    pages = PageCollection(session)
    root = pages.add_root("Root")
    assert pages.query().filter(
        Page.publication_started == True,
        Page.publication_ended == False
    ).one()

    page = pages.add(parent=root, title='Article', type='article')
    assert isinstance(page, Article)
    assert page.published_or_created
    assert page.published

    page = pages.add(parent=root, title='Page')
    assert not isinstance(page, Article)

    with pytest.raises(AssertionError) as assertion_info:
        page = pages.add(parent=root, title='Test', type='undefined')

    assert "No such polymorphic_identity" in str(assertion_info.value)

    assert isinstance(pages.by_path('/root/article'), Article)
    assert not isinstance(pages.by_path('/root/page'), Article)

    assert "No such polymorphic_identity" in str(assertion_info.value)

    assert pages.by_path('/root/article')
    assert pages.by_path('/root/article', ensure_type='article')
    assert not pages.by_path('/root/article', ensure_type='missing')
    assert not pages.by_path('/root/inexistant', ensure_type='article')
