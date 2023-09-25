from functools import lru_cache


@lru_cache(maxsize=1)
def show_tags(request):
    return request.app.org.event_filter_type in ['tags', 'tags_and_filters']


@lru_cache(maxsize=1)
def show_filters(request):
    return request.app.org.event_filter_type in ['filters', 'tags_and_filters']
