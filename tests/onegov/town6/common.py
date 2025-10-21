from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import ExtendedResponse


def step_class(page: ExtendedResponse, step: int) -> str:
    return page.pyquery(f'[data-step="{step}"]').attr('class')
