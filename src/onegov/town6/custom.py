from onegov.org.custom import get_global_tools as get_global_tools_base


def get_global_tools(request):
    for item in get_global_tools_base(request):

        if getattr(item, 'attrs', {}).get('class') == {'login'}:
            continue

        yield item
