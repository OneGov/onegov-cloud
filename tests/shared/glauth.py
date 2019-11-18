import port_for

from attr import attrs, attrib
from onegov.core.utils import Bunch
from pathlib import Path
from tempfile import NamedTemporaryFile
from mirakuru import TCPExecutor
from textwrap import dedent


@attrs(auto_attribs=True)
class GLAuth(object):
    """ Runs an LDAP sever using glauth.

    Requires the path to the glauth binary (can be retrieved through the
    `glauth_binary` fixture) and a valid configuration.

    Should be used as follows::

        with GLAuth(glauth_binary, config):
            # test ldap code

    Inside the config, use '%(port)s' and '%(host)s', which will be substituted
    with the port/host the ldap server is running under. Though the host should
    usually be 'localhost', the port is random every time.

    To get the host/port::
        with GLAuth(glauth_binary, config) as auth:
            auth.context.host
            auth.context.port

    Note, to use ldaps, a certifiacte is required. The following should do::

        from onegov.core.utils import module_path

        cert_file = module_path('tests.shared', 'fixtures/self-signed.crt')
        cert_key = module_path('tests.shared', 'fixtures/self-signed.key')

    """

    glauth_binary: Path = attrib(converter=Path)
    glauth_config: str

    def __enter__(self):
        self.context = Bunch()

        # pick the socket
        self.context.host = '127.0.0.1'
        self.context.port = port_for.select_random()

        # write the config
        self.context.config = config = NamedTemporaryFile(mode='w')
        config.write(dedent(self.glauth_config % {
            'host': self.context.host,
            'port': self.context.port,
        }))
        config.flush()

        # start the server
        self.context.executor = TCPExecutor(
            f'{self.glauth_binary} -c {config.name}',
            self.context.host,
            self.context.port)

        # wait for it to be running
        self.context.executor.start()

        return self

    def __exit__(self, *args, **kwargs):

        # stop the server
        self.context.executor.stop()
        self.context.executor.kill()

        # delete the temporary files
        del self.context
