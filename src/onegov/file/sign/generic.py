from __future__ import annotations

import os.path

from contextlib import contextmanager, suppress
from tempfile import mkstemp
from io import UnsupportedOperation


from typing import Any, ClassVar, Protocol, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRead, SupportsWrite
    from collections.abc import Iterator
    from onegov.file.types import SigningServiceConfig

    class SupportsReadAndHasName(SupportsRead[bytes], Protocol):
        @property
        def name(self) -> str: ...


class SigningService:
    """ A generic interface for various file signing services. """

    registry: ClassVar[dict[str, type[SigningService]]] = {}
    service_name: ClassVar[str]

    def __init_subclass__(cls, service_name: str, **kwargs: Any):
        SigningService.registry[service_name] = cls
        cls.service_name = service_name

        super().__init_subclass__(**kwargs)

    @staticmethod
    def for_config(config: SigningServiceConfig) -> SigningService:
        """ Spawns a service instance using the given config. """

        return SigningService.registry[config['name']](
            **config.get('parameters', {})
        )

    def __init__(self, **parameters: Any):
        """ Signing services are initialised with parameters of their chosing.

        Typically those parameters are read from a yaml file::

            name: service_name
            paramters:
                foo: bar
                bar: foo

        This function may be overwritten by the subclass with concrete
        arguemnts. For example::

            class MyService(SigningService, name='my_service'):

                def __init__(self, user, password):
                    pass

        During initialisiation through onegov.file.integration (and only then),
        the current path is set to the path of the config file.

        """

        self.parameters = parameters

    def sign(
        self,
        infile: SupportsRead[bytes],
        outfile: SupportsWrite[bytes]
    ) -> str:
        """ Signs the input file and writes it to the given output file.

        Arguments
        =========

        If the input-file exists on disk, its ``file.name`` attribute points
        to an existing path.

        Sublcasses may add extra parameters to this signing function, though
        it is expected that they all have a default value set.

        So it is okay to do this::

            def sign(self, infile, outfile, foo)

        But it would be better to do thiss::

            def sign(self, infile, outfile, foo='bar')

        Return Value
        ============

        The sign function *must* return a unique request id for each signed
        file. This function should be composed of the service name and a
        unique identifier. For example: 'my_service/0b86854'. Using this
        identifier it should be possible to query the signing service backend
        for more information (in case we ever need to investigate).

        It is up to the signing service to know what should be part of this
        unique identifer. The only thing that can't be part of the identifer
        are secrets.

        """

        raise NotImplementedError

    @contextmanager
    def materialise(
        self,
        file: SupportsRead[bytes]
    ) -> Iterator[SupportsReadAndHasName]:
        """ Takes the given file-like object and ensures that it exists
        somewhere on the disk during the lifetime of the context.

        """
        if hasattr(file, 'seek'):
            with suppress(UnsupportedOperation):
                file.seek(0)

        if hasattr(file, 'name') and os.path.exists(file.name):
            yield file  # type:ignore[misc]
        else:
            _fd, path = mkstemp()

            with open(path, 'rb+') as output:
                output.writelines(iter(lambda: file.read(4096), b''))

                output.seek(0)

                yield output

            os.unlink(path)
