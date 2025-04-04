from collections.abc import Callable, Sequence
from types import ModuleType

def scan(package: ModuleType | None = None, ignore: Sequence[Callable[[str], bool] | str] | None = None, handle_error: Callable[[str, Exception], object] | None = None) -> None: ...
def autoscan(ignore: Sequence[Callable[[str], bool] | str] | None = None) -> None: ...
