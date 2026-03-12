from __future__ import annotations

import pytest
import transaction

from onegov.core.utils import Bunch, normalize_for_url
from onegov.org.models.page import NewsCollection
from onegov.org.models import News
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from sqlalchemy.orm.unitofwork import UOWTransaction


@pytest.mark.parametrize("item_count", [1000])  # Parameterize if needed later
def test_add_performance_large_collection(
    item_count: int,
    session: Session
) -> None:
    """
    Previously, we encountered a performance issue with our AdjacencyList
    implementation. When news items were sorted alphabetically by sort key,
    adding a single new item (such as one titled 'AAAAAAA') to a large
    NewsCollection (around a thousand items) would trigger extensive reordering
    throughout the tree structure.

    Subsequently all these 'order' updates would be consumed in the update
    queue from of `Indexer`, amplifying the problem.

    To tackle this problem, we have now a smarter insertion method,
    starting at the midpoint.

    So this test verifies that adding one item is fast and doesn't scale
    linearly with the number of existing items (i.e., avoids O(N) updates
    to all ordering).
    """


    def add_news(session: Session) -> int:
        root_title = 'Aktuelles'
        root_name = normalize_for_url(root_title)
        root_item = News(title=root_title, name=root_name, type='news')
        session.add(root_item)
        session.flush()
        root_item_id = root_item.id
        for i in range(item_count):
            title = f'News Item {i:04d}'
            name = normalize_for_url(title)
            item = News(title=title, name=name, type='news', parent=root_item)
            session.add(item)

        transaction.commit()
        return root_item_id

    root_item_id = add_news(session)

    root_item = session.query(News).filter_by(id=root_item_id).one()
    request: Any = Bunch(session=session)
    news_collection = NewsCollection(request, root=root_item)
    new_item_data: dict[str, Any] = {
        'parent': root_item,
        'title': 'AAAAAAA',
        'lead': '',
        'text': ''
    }

    update_counter = {'count': 0}

    # Event listener function to count News.order updates
    def count_order_updates(
        session: Session,
        flush_context: UOWTransaction
    ) -> None:
        for instance in session.dirty:
            if isinstance(instance, News):
                # Check if 'order' attribute is changing
                hist = get_history(instance, 'order')
                if hist.has_changes():
                    update_counter['count'] += 1

    event.listen(session, 'after_flush', count_order_updates)

    try:
        # Add the item using the collection's method - this triggers the logic
        new_item = news_collection.add(**new_item_data)
        session.flush()  # Trigger the flush and the listener
    finally:
        event.remove(session, 'after_flush', count_order_updates)

    # The crucial assertion: Add one item should cause very few order updates
    # The midpoint strategy might update the item and potentially one neighbor.
    # Allow a small buffer, but it should be constant, not O(N).
    #
    # Note: Before the fix in OGC-2134, this created a thousand updates!
    max_expected_updates = 5
    assert update_counter['count'] <= max_expected_updates, (
        f"Adding one item caused {update_counter['count']} 'order' updates, "
        f"expected <= {max_expected_updates}. Possible O(N) update issue?"
    )
