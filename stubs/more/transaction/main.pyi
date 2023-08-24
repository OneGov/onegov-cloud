from collections.abc import Callable
from typing import Any

from morepath import App
from morepath.request import Request
from morepath.response import Response

class TransactionApp(App): ...

def default_commit_veto(request: Request, response: Response) -> bool: ...

class AbortResponse(Exception):
    response: Response
    def __init__(self, response: Response) -> None: ...

def get_transaction_settings() -> dict[str, Any]: ...
def transaction_tween_factory(app: TransactionApp, handler: Callable[[Request], Response]) -> Callable[[Request], Response]: ...
