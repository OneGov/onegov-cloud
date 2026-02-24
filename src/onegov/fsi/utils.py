from __future__ import annotations


def handle_empty_p_tags(html: str) -> str:
    return html if html != '<p></p>' else ''
