from _typeshed.wsgi import StartResponse, WSGIEnvironment
from collections.abc import Callable, Iterable, Iterator
from typing import Any, TypeVar, overload

from dectate.app import App as DectateApp, directive
from morepath import directive as action, reify
from morepath.authentication import Identity, NoIdentity
from morepath.request import Request, Response
from morepath.settings import SettingRegistry
from reg.cache import DictCachingKeyLookup
from reg.context import dispatch_method as _dispatch_method
from reg.dispatch import _GetKeyLookup, _KeyLookup
from reg.predicate import Predicate
from webob.response import Response as BaseResponse

_AppT = TypeVar('_AppT', bound=App)

def cached_key_lookup(key_lookup: _KeyLookup) -> DictCachingKeyLookup: ...
def commit_if_needed(app: App) -> None: ...
def dispatch_method(*predicates: str | Predicate, get_key_lookup: _GetKeyLookup = ..., first_invocation_hook: Callable[[Any], object] = ...) -> _dispatch_method[Any, Any, Any]: ...

class App(DectateApp):
    parent: App | None
    request_class: type[Request]
    logger_name: str
    setting = directive(action.SettingAction)
    setting_section = directive(action.SettingSectionAction)
    predicate_fallback = directive(action.PredicateFallbackAction)
    predicate = directive(action.PredicateAction)
    method = directive(action.MethodAction)
    converter = directive(action.ConverterAction)
    _path = directive(action.PathAction)
    path = directive(action.PathCompositeAction)
    permission_rule = directive(action.PermissionRuleAction)
    template_directory = directive(action.TemplateDirectoryAction)
    template_loader = directive(action.TemplateLoaderAction)
    template_render = directive(action.TemplateRenderAction)
    view = directive(action.ViewAction)
    json = directive(action.JsonAction)
    html = directive(action.HtmlAction)
    mount = directive(action.MountAction)
    defer_links = directive(action.DeferLinksAction)
    defer_class_links = directive(action.DeferClassLinksAction)
    tween_factory = directive(action.TweenFactoryAction)
    identity_policy = directive(action.IdentityPolicyAction)
    verify_identity = directive(action.VerifyIdentityAction)
    dump_json = directive(action.DumpJsonAction)
    link_prefix = directive(action.LinkPrefixAction)
    def __init__(self) -> None: ...
    def request(self, environ: WSGIEnvironment) -> Request: ...
    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> Iterable[bytes]: ...
    @reify
    def publish(self) -> Callable[[Request], Response]: ...
    def ancestors(self) -> Iterator[App]: ...
    @reify
    def root(self) -> App: ...
    @overload
    def child(self, app: _AppT) -> _AppT | None: ...
    @overload
    def child(self, app: type[_AppT], **variables: Any) -> _AppT | None: ...
    @overload
    def child(self, app: str, **variables: Any) -> App: ...
    @overload
    def sibling(self, app: _AppT) -> _AppT | None: ...
    @overload
    def sibling(self, app: type[_AppT], **variables: Any) -> _AppT | None: ...
    @overload
    def sibling(self, app: str, **variables: Any) -> App: ...
    @property
    def settings(self) -> SettingRegistry: ...
    @classmethod
    def mounted_app_classes(cls, callback: Callable[..., Any] | None = None) -> set[type[App]]: ...
    @classmethod
    def commit(cls) -> set[type[App]]: ...
    @classmethod
    def init_settings(cls, settings: dict[str, dict[str, Any]]) -> None: ...
    @dispatch_method()
    def get_view(self, obj: object, request: Request) -> BaseResponse: ...
    @dispatch_method()
    def _permits(self, identity: Identity | NoIdentity, obj: object, permission: object) -> bool: ...
    @classmethod
    def clean(cls) -> None: ...
    def remember_identity(self, response: BaseResponse, request: Request, identity: Identity) -> None: ...
    def forget_identity(self, response: BaseResponse, request: Request) -> None: ...
