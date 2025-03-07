import abc

from .request import Request, Response

class NoIdentity:
    userid: None

NO_IDENTITY: NoIdentity

# NOTE: Technically the actual Identity class is more generic and generates
#       attributes based on what's passed to __init__, but for simplicity we
#       assume the arguments we will pass in so we can type check them. If
#       we wanted to ship these type stubs we would need to make this more
#       generic again.
class Identity:
    userid: str  # email
    uid: str  # actual user id
    groupids: frozenset[str]
    role: str
    application_id: str
    verified: bool | None
    def __init__(self, userid: str, *, uid: str, groupids: frozenset[str], role: str, application_id: str) -> None: ...
    def as_dict(self) -> dict[str, str]: ...

class IdentityPolicy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def identify(self, request: Request) -> Identity | NoIdentity: ...
    @abc.abstractmethod
    def remember(self, response: Response, request: Request, identity: Identity) -> None: ...
    @abc.abstractmethod
    def forget(self, response: Response, request: Request) -> None: ...
