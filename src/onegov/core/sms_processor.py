"""
Send SMS through ASPSMS

Adapted from `repoze.sendmail<https://github.com/repoze/repoze.sendmail>`_.

Usage::
    qp = SmsQueueProcessor(sms_directory)
    qp.send_messages()
"""
from __future__ import annotations

import errno
import logging
import json
import os
import pycurl
import stat
import time

from io import BytesIO


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.core.framework import Framework
    from onegov.core.types import JSON_ro


log = logging.getLogger('onegov.core')


# The below diagram depicts the operations performed while sending a message.
# This sequence of operations will be performed for each file in the maildir
# on which ``send_message`` is called.
#
# Any error conditions not depected on the diagram will provoke the catch-all
# exception logging of the ``send_message`` method.
#
# In the diagram the "message file" is the file in the maildir's "cur"
# directory that contains the message and "tmp file" is a hard link to the
# message file created in the maildir's "tmp" directory.
#
#           ( start trying to deliver a message )
#                            |
#                            |
#                            V
#            +-----( get tmp file mtime )
#            |               |
#            |               | file exists
#            |               V
#            |         ( check age )-----------------------------+
#   tmp file |               |                       file is new |
#   does not |               | file is old                       |
#   exist    |               |                                   |
#            |      ( unlink tmp file )-----------------------+  |
#            |               |                      file does |  |
#            |               | file unlinked        not exist |  |
#            |               V                                |  |
#            +---->( touch message file )------------------+  |  |
#                            |                   file does |  |  |
#                            |                   not exist |  |  |
#                            V                             |  |  |
#            ( link message file to tmp file )----------+  |  |  |
#                            |                 tmp file |  |  |  |
#                            |           already exists |  |  |  |
#                            |                          |  |  |  |
#                            V                          V  V  V  V
#                     ( send message )             ( skip this message )
#                            |
#                            V
#                 ( unlink message file )---------+
#                            |                    |
#                            | file unlinked      | file no longer exists
#                            |                    |
#                            |  +-----------------+
#                            |  |
#                            |  V
#                  ( unlink tmp file )------------+
#                            |                    |
#                            | file unlinked      | file no longer exists
#                            V                    |
#                  ( message delivered )<---------+


# The longest time sending a file is expected to take.  Longer than this and
# the send attempt will be assumed to have failed.  This means that sending
# very large files or using very slow mail servers could result in duplicate
# messages sent.
MAX_SEND_TIME = 60 * 60 * 3


class SmsQueueProcessor:

    def __init__(
        self,
        path: str,
        username: str,
        password: str,
        originator: str | None = None
    ):
        self.path = path
        self.username = username
        self.password = password
        self.originator = originator or 'OneGov'

        # Keep a pycurl object around, to use HTTP keep-alive - though pycurl
        # is much worse in terms of it's API, the performance is *much* better
        # than requests and it supports modern features like HTTP/2 or HTTP/3
        self.url = 'https://json.aspsms.com/SendSimpleTextSMS'
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.TCP_KEEPALIVE, 1)
        self.curl.setopt(pycurl.URL, self.url)
        self.curl.setopt(pycurl.HTTPHEADER, ['Content-Type:application/json'])
        self.curl.setopt(pycurl.POST, 1)

    def split(self, filename: str) -> tuple[str, str, str]:
        """ Returns the path, the name and the suffix of the given path. """

        if '/' in filename:
            path, name = filename.rsplit('/', 1)
        else:
            path = ''
            name = filename

        if '.' in name:
            name, suffix = name.split('.', 1)
        else:
            suffix = ''

        return path, name, suffix

    def message_files(self) -> tuple[str, ...]:
        """ Returns a tuple of full paths that need processing.

        The file names in the directory usually look like this:

            * 0.1571822840.745629
            * 1.1571822743.595377

        The part before the first dot is the batch number the rest is
        the timestamp at time of calling app.send_sms.

        The messages are sorted by suffix, so by default the sorting
        happens from oldest to newest message.

        """
        files = []

        for f in os.scandir(self.path):

            if not f.is_file():
                continue

            # ignore .sending- .rejected-  files
            if f.name.startswith('.'):
                continue

            files.append(f)

        files.sort(key=lambda i: self.split(i.name)[-1])

        return tuple(os.path.join(self.path, f.name) for f in files)

    def send(
        self,
        numbers: Sequence[str],
        content: str
    ) -> dict[str, Any] | None:
        """ Sends the SMS and returns the API response on error.

        On success this returns None.
        """
        code, body = self.send_request({
            'UserName': self.username,
            'Password': self.password,
            'Originator': self.originator,
            'Recipients': numbers,
            'MessageText': content,
        })

        if 400 <= code < 600:
            raise RuntimeError(f'{code} calling {self.url}: {body}')

        result = json.loads(body)

        if result.get('StatusInfo') != 'OK' or result.get('StatusCode') != '1':
            return result
        return None

    def send_request(self, parameters: JSON_ro) -> tuple[int, str]:
        """ Performes the API request using the given parameters. """

        body = BytesIO()

        self.curl.setopt(pycurl.WRITEDATA, body)
        self.curl.setopt(pycurl.POSTFIELDS, json.dumps(parameters))
        self.curl.perform()

        code = self.curl.getinfo(pycurl.RESPONSE_CODE)

        body.seek(0)
        body_str = body.read().decode('utf-8')

        return code, body_str

    def parse(
        self,
        filename: str
    ) -> tuple[tuple[str, ...] | None, str | None]:

        with open(filename) as f:
            try:
                data = json.loads(f.read())
            except json.JSONDecodeError:
                return None, None

        if not isinstance(data, dict):
            return None, None

        receivers = data.get('receivers')
        content = data.get('content')
        if not isinstance(receivers, list):
            return None, content

        # NOTE: For now we silently drop invalid numbers in a batch
        #       maybe we want to fail instead in this case.
        #       This should only really come into play if someone
        #       messes with the file contents in an editor.
        #       Numbers stored in the system are pre-validated.
        receivers = tuple(
            r for r in receivers
            if isinstance(r, str) and r.lstrip('+').isdigit()
        )

        return receivers, content

    def send_messages(self) -> None:
        for filename in self.message_files():
            self.send_message(filename)

    def send_message(self, filename: str) -> None:
        head, tail = os.path.split(filename)
        tmp_filename = os.path.join(head, f'.sending-{tail}')
        rejected_filename = os.path.join(head, f'.rejected-{tail}')
        failed_filename = os.path.join(head, f'.failed-{tail}')

        # perform a series of operations in an attempt to ensure
        # that no two threads/processes send this message
        # simultaneously as well as attempting to not generate
        # spurious failure messages in the log; a diagram that
        # represents these operations is included in a
        # comment above this class
        try:
            # find the age of the tmp file (if it exists)
            mtime = os.stat(tmp_filename)[stat.ST_MTIME]
        except OSError as e:
            if e.errno == errno.ENOENT:
                # file does not exist
                # the tmp file could not be stated because it
                # doesn't exist, that's fine, keep going
                age = None
            else:
                # the tmp file could not be stated for some reason
                # other than not existing; we'll report the error
                raise
        else:
            age = time.time() - mtime

        # if the tmp file exists, check it's age
        if age is not None:
            try:
                if age > MAX_SEND_TIME:
                    # the tmp file is "too old"; this suggests
                    # that during an attemt to send it, the
                    # process died; remove the tmp file so we
                    # can try again
                    os.remove(tmp_filename)
                else:
                    # the tmp file is "new", so someone else may
                    # be sending this message, try again later
                    return
                # if we get here, the file existed, but was too
                # old, so it was unlinked
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # file does not exist
                    # it looks like someone else removed the tmp
                    # file, that's fine, we'll try to deliver the
                    # message again later
                    return

        # now we know that the tmp file doesn't exist, we need to
        # "touch" the message before we create the tmp file so the
        # mtime will reflect the fact that the file is being
        # processed (there is a race here, but it's OK for two or
        # more processes to touch the file "simultaneously")
        try:
            os.utime(filename, None)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # file does not exist
                # someone removed the message before we could
                # touch it, no need to complain, we'll just keep
                # going
                return
            else:
                # Some other error, propogate it
                raise

        # creating this hard link will fail if another process is
        # also sending this message
        try:
            os.link(filename, tmp_filename)
        except OSError as e:
            if e.errno == errno.EEXIST:
                # file exists, *nix
                # it looks like someone else is sending this
                # message too; we'll try again later
                return
            else:
                # Some other error, propogate it
                raise

        # read message file and send contents
        numbers, message = self.parse(filename)
        if numbers and message:
            status = self.send(numbers, message)
            if status is None:
                log.info('SMS to {} sent.'.format(', '.join(numbers)))
            else:
                # this should cause stderr output, which
                # will write the cronjob output to chat
                log.error(
                    f'Failed sending SMS batch {filename} with '
                    f'API response {status}'
                )
                os.link(filename, failed_filename)
        else:
            # this should cause stderr output, which
            # will write the cronjob output to chat
            log.error(
                f'Discarding SMS batch {filename} due to invalid '
                'content/numbers'
            )
            os.link(filename, rejected_filename)

        try:
            os.remove(filename)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # file does not exist
                # someone else unlinked the file; oh well
                pass
            else:
                # something bad happend, log it
                raise

        try:
            os.remove(tmp_filename)
        except OSError as e:
            if e.errno == errno.ENOENT:
                # file does not exist
                # someone else unlinked the file; oh well
                pass
            else:
                # something bad happened, log it
                raise


def get_sms_queue_processor(
    app: Framework,
    missing_path_ok: bool = False
) -> SmsQueueProcessor | None:

    if not app.can_deliver_sms:
        return None

    username = app.sms.get('user')
    password = app.sms.get('password')
    originator = app.sms.get('originator')
    tenants = app.sms.get('tenants', {})
    sms = tenants.get(app.application_id, tenants.get(app.namespace))
    if sms is not None:
        username = sms.get('user', username)
        password = sms.get('password', password)
        originator = sms.get('originator', originator)
    elif username is None:
        return None

    assert app.sms_directory
    assert username is not None and password is not None
    path = os.path.join(app.sms_directory, app.schema)
    path = os.path.abspath(path)
    if missing_path_ok or os.path.exists(path):
        return SmsQueueProcessor(
            path,
            username,
            password,
            originator
        )

    return None
