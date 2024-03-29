from dectate.config import Action, CodeInfo

class ConfigError(Exception): ...

def conflict_keyfunc(action: Action) -> tuple[str, int]: ...

class ConflictError(ConfigError):
    actions: list[Action]
    def __init__(self, actions: list[Action]) -> None: ...

class DirectiveReportError(ConfigError):
    def __init__(self, message: str, code_info: CodeInfo) -> None: ...

class DirectiveError(ConfigError): ...
class TopologicalSortError(ValueError): ...
class QueryError(Exception): ...
