def handle_empty_p_tags(html):
    return html if not html == '<p></p>' else ''
