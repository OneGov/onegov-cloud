from .arginfo import arginfo as arginfo
from .cache import DictCachingKeyLookup as DictCachingKeyLookup, LruCachingKeyLookup as LruCachingKeyLookup
from .context import (
    DispatchMethod as DispatchMethod,
    clean_dispatch_methods as clean_dispatch_methods,
    dispatch_method as dispatch_method,
    methodify as methodify,
)
from .dispatch import Dispatch as Dispatch, LookupEntry as LookupEntry, dispatch as dispatch
from .error import RegistrationError as RegistrationError
from .predicate import (
    ClassIndex as ClassIndex,
    KeyIndex as KeyIndex,
    Predicate as Predicate,
    match_class as match_class,
    match_instance as match_instance,
    match_key as match_key,
)
