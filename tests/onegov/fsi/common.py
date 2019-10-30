def collection_attr_eq_test(collection, other_collection):
    # Tests a collection of the method page_by_index duplicates all attrs
    for key in collection.__dict__:
        if key in ('page', 'cached_subset', 'batch'):
            continue
        assert getattr(collection, key) == getattr(other_collection, key)
