import pytest
import time

from onegov.core.utils import Bunch
from onegov.org.models import News, NewsCollection
from onegov.core.utils import normalize_for_url


@pytest.mark.parametrize("item_count", [1000])  # Parameterize if needed later
def test_add_performance_large_collection(session, item_count):
    """
    Previously we had the following issue:
    AdjacencyList items were sorted alphabetically by sort key. When we
    had 1200 news items (not unusual in real world scenarios) and
    created a news item with title 'AAAAAAA', depending on the tree
    structure, the order was adjusted for a lot of news items.
    Everything went into the ORM update queue from the Indexer, creating
    a delay of several seconds.

    To tackle this problem, we have now a smarter insertion method, starting
    at the midpoint.

    So this test verifies that adding one item is fast and doesn't scale
    linearly with the number of existing items (i.e., avoids O(N) updates
    to all ordering).
    """

    request = Bunch(session=session)
    news_collection = NewsCollection(request)

    start_setup = time.perf_counter()
    for i in range(item_count):
        # Use unique titles to ensure they spread out in initial order
        title = f'News Item {i:04d}'
        title = normalize_for_url(title)
        # Add as root items for simplicity, adjust if parent is required
        item = News(title=title, name=title, type='news')
        session.add(item)
        # Flush periodically to manage transaction size
        if i % 100 == 99:
            print(f'  Flushing at item {i + 1}...')
            session.flush()

    # Final flush and commit to persist the initial items
    session.flush()
    end_setup = time.perf_counter()
    print(f'Setup took {end_setup - start_setup:.4f} seconds.')

    # --- Timed Addition Phase ---
    title_to_add = (
        'AAAAAA Very First News'  # Title designed to go near the start
    )
    print(f"Timing the addition of one news item ('{title_to_add}')...")

    start_add = time.perf_counter()

    # Add one item using the collection method
    new_item = news_collection.add(
        parent=None, title=title_to_add
    )  # Add as root
    session.flush()  # Ensure the add operation (incl. order calc and DB write) completes

    end_add = time.perf_counter()
    duration_add = end_add - start_add

    print(f'Adding one item took {duration_add:.6f} seconds.')

    # --- Verification ---
    # Check the item was added
    assert new_item is not None
    assert new_item.title == title_to_add
    # Fetch from DB to be sure
    fetched_item = session.query(News).get(new_item.id)
    assert fetched_item is not None

    # The crucial assertion: Adding one item should be very fast.
    # Set a generous threshold (e.g., 0.5 seconds). If it takes longer,
    # it suggests the O(N) update problem might still exist.
    # Adjust threshold based on your system/DB performance, but it should
    # be significantly less than the setup time or multiple seconds.
    threshold = 0.5
    assert duration_add < threshold, (
        f'Adding one item took too long ({duration_add:.6f}s), '
        f'expected less than {threshold}s. Possible O(N) update issue?'
    )

    # Optional: Clean up if session fixture doesn't handle it fully
    # (e.g., if using a persistent test DB)
    # print("Cleaning up...")
    # session.query(News).delete()
    # session.commit()
