def swap_layout(response, layout):
    if isinstance(response, dict) and response.get('layout'):
        response['layout'] = layout
        return response
    return response