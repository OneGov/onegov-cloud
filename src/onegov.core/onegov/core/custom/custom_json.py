""" Sigh. Here we go again, *another* json implementation with support for:

- date
- datetime
- time

Because nobody else does all of these. And if they do (like standardjson), they
don't support decoding...

"""

import datetime
import isodate
import re

from decimal import Decimal
from itertools import chain
from onegov.core.cache import lru_cache
from rapidjson import Decoder as RapidJsonDecoder
from rapidjson import Encoder as RapidJsonEncoder


class Serializer(object):
    """ Provides a way to encode all objects of a given class or its
    subclasses to and from json.

    """

    def __init__(self, target):
        assert isinstance(target, type), "expects a class"
        self.target = target

    def encode(self, obj):
        raise NotImplementedError

    def decode(self, value):
        raise NotImplementedError


class PrefixSerializer(Serializer):
    """ Serializes objects to a string with a prefix.

    Resulting json values take the form of __prefix__@<value>, where <value>
    is the encoded value and __prefix__@ is the prefix that is used to
    differentiate between normal strings and encoded strings.

    Note that the part after the prefix is user-supplied and possibly unsafe.
    So something like an 'eval' should be out of the question!

    """

    prefix_format = '__{}__@{}'
    prefix_expression = re.compile(r'__(?P<prefix>[a-zA-Z]+)__@')
    prefix_characters = re.compile(r'[a-zA-Z-]+')

    def __init__(self, target, prefix, encode, decode):
        super().__init__(target)

        assert self.prefix_characters.match(prefix)

        self.prefix = prefix
        self.prefix_length = len(self.prefix_format.format(prefix, ''))
        self._encode = encode
        self._decode = decode

    def encode(self, obj):
        return '__{}__@{}'.format(self.prefix, self._encode(obj))

    def decode(self, string):
        return self._decode(string[self.prefix_length:])


class DictionarySerializer(Serializer):
    """ Serialises objects that can be built with keyword arguments.

    For example::

        class Point(object):

            def __init__(self, x, y):
                self.x = x
                self.y = y

    Can be serialised using::

        DictionarySerializer(Point, ('x', 'y'))

    Which results in something like this in JSON::

        {'x': 1, 'y': 2}

    As the internal __dict__ represenation is of no concern, __slots__ may
    be used:

        class Point(object):

            __slots__ = ('x', 'y')

            def __init__(self, x, y):
                self.x = x
                self.y = y

    """

    def __init__(self, target, keys):
        super().__init__(target)

        self.keys = frozenset(keys)

    def encode(self, obj):
        return {k: getattr(obj, k) for k in self.keys}

    def decode(self, dictionary):
        return self.target(**dictionary)


class Serializers(object):
    """ Organises the different serializer implementations under a unifiying
    interface. This allows the actual encoder/decoder to call a single class
    without having to worry how the various serializers need to be looked up
    and called.

    """

    def __init__(self):
        self.by_prefix = {}
        self.by_keys = {}
        self.known_key_lengths = set()

    @property
    def registered(self):
        return chain(self.by_prefix.values(), self.by_keys.values())

    def register(self, serializer):
        if isinstance(serializer, PrefixSerializer):
            self.by_prefix[serializer.prefix] = serializer

        elif isinstance(serializer, DictionarySerializer):
            self.by_keys[serializer.keys] = serializer
            self.known_key_lengths.add(len(serializer.keys))

        else:
            raise NotImplementedError

    def serializer_for(self, value):
        if isinstance(value, str):
            return self.serializer_for_string(value)

        if isinstance(value, dict):
            return self.serializer_for_dict(value)

        if isinstance(value, type):
            return self.serializer_for_class(value)

    def serializer_for_string(self, string):
        match = PrefixSerializer.prefix_expression.match(string)
        return self.by_prefix.get(match.group('prefix') if match else None)

    def serializer_for_dict(self, dictionary):

        # we can exit early for all dictionaries which cannot possibly match
        # the keys we're looking for by comparing the number of keys in the
        # dictionary - this is much cheaper than the next lookup
        if len(dictionary.keys()) not in self.known_key_lengths:
            return

        return self.by_keys.get(frozenset(dictionary.keys()))

    @lru_cache(maxsize=16)
    def serializer_for_class(self, cls):
        matches = (s for s in self.registered if issubclass(cls, s.target))
        return next(matches, None)

    def encode(self, value):
        serializer = self.serializer_for(value.__class__)

        if serializer:
            return serializer.encode(value)

        raise TypeError('{} is not JSON serializable'.format(repr(value)))

    def decode(self, value):
        serializer = self.serializer_for(value)

        if serializer:
            return serializer.decode(value)

        return value


# The builtin serializers
default_serializers = Serializers()

default_serializers.register(PrefixSerializer(
    prefix='datetime',
    target=datetime.datetime,
    encode=isodate.datetime_isoformat,
    decode=isodate.parse_datetime
))

default_serializers.register(PrefixSerializer(
    prefix='time',
    target=datetime.time,
    encode=isodate.time_isoformat,
    decode=isodate.parse_time
))

default_serializers.register(PrefixSerializer(
    prefix='date',
    target=datetime.date,
    encode=isodate.date_isoformat,
    decode=isodate.parse_date
))

default_serializers.register(PrefixSerializer(
    prefix='decimal',
    target=Decimal,
    encode=str,
    decode=Decimal
))


class Serializable(object):
    """ Classes inheriting from this base are serialised using the
    :class:`DictionarySerializer` class.

    The keys that should be used need to be specified as follows::

        class Point(Serializable, keys=('x', 'y')):

            def __init__(self, x, y):
                self.x = x
                self.y = y

    """

    @classmethod
    def serializers(cls):
        return default_serializers  # for testing

    def __init_subclass__(cls, keys, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.serialized_keys = keys
        cls.serializers().register(DictionarySerializer(
            target=cls,
            keys=keys
        ))


class Encoder(RapidJsonEncoder):

    def __init__(self, *args, **kwargs):
        self.serializers = kwargs.pop('serializers', default_serializers)
        super().__init__()

    def default(self, o):
        return self.serializers.encode(o)


class Decoder(RapidJsonDecoder):

    def __init__(self, *args, **kwargs):
        self.serializers = kwargs.pop('serializers', default_serializers)
        super().__init__()

    def string(self, value):
        return self.serializers.decode(value)

    def end_object(self, value):
        return self.serializers.decode(value)


def dumps(obj, *args, **kwargs):
    if obj is not None:
        return Encoder(*args, **kwargs)(obj)
    else:
        return None


def loads(value, *args, **kwargs):
    if value is not None:
        return Decoder(*args, **kwargs)(value)
    else:
        return {}


def dump(data, fp, *args, **kwargs):
    return fp.write(dumps(data, *args, **kwargs))


def load(fp, *args, **kwargs):
    return loads(fp.read(), *args, **kwargs)
