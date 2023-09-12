from dectate import (
    ConfigError,
    ConflictError as ConflictError,
    DirectiveError as DirectiveError,
    DirectiveReportError as DirectiveReportError,
    TopologicalSortError as TopologicalSortError,
)

class AutoImportError(ConfigError):
    def __init__(self, module_name: str) -> None: ...

class TrajectError(Exception): ...
class LinkError(Exception): ...
