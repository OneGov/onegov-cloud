"""
    Send SMS through ASPSMS

    Adapted from repoze.sendmail: https://github.com/repoze/repoze.sendmail

    Usage:
        qp = SmsQueueProcessor(sms_directory)
        qp.send_messages()
"""

import errno
import logging
import os
import stat
import time
import requests

from raven import Client


log = logging.getLogger('onegov.election_day')


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


class SmsQueueProcessor(object):

    def __init__(self, path, username, password, sentry_dsn=None,
                 originator=None):
        self.path = path
        self.username = username
        self.password = password
        self.sentry_client = Client(sentry_dsn) if sentry_dsn else None
        self.originator = originator or "OneGov"

    def _send(self, number, content):
        response = requests.post(
            'https://json.aspsms.com/SendSimpleTextSMS',
            json={
                "UserName": self.username,
                "Password": self.password,
                "Originator": self.originator,
                "Recipients": [number],
                "MessageText": content
            }
        )

        response.raise_for_status()
        result = response.json()
        if result['StatusInfo'] != 'OK' or result['StatusCode'] != '1':
            raise

    def _parseMessage(self, filename):
        number = None
        message = None
        parts = os.path.basename(filename).split('.')
        if len(parts):
            if parts[0].startswith('+'):
                if all(c.isdigit() for c in parts[0][1:]):
                    number = parts[0]

        with open(filename) as f:
            message = f.read()

        return number, message

    def send_messages(self):
        # We expect to messages to in E.164 format, eg. '+41780000000'
        messages = [
            os.path.join(self.path, x) for x in os.listdir(self.path)
            if x.startswith('+')
        ]

        # Sort by modification time so earlier messages are sent before
        # later messages during queue processing.
        messages = [(m, os.path.getmtime(m)) for m in messages]
        messages.sort(key=lambda x: x[1])
        for filename, timestamp in messages:
            self._send_message(filename)

    def _send_message(self, filename):
        head, tail = os.path.split(filename)
        tmp_filename = os.path.join(head, '.sending-' + tail)
        rejected_filename = os.path.join(head, '.rejected-' + tail)
        try:
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
            number, message = self._parseMessage(filename)
            if number and message:
                self._send(number, message)
            else:
                log.error(
                    "Discarding SMS {} due to invalid content/number".format(
                        filename
                    )
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

            log.info("SMS to {} sent.".format(number))

        # Catch errors and log them here
        except:
            if self.sentry_client:
                self.sentry_client.captureException()
            else:
                log.error(
                    "Error while sending SMS {}".format(filename),
                    exc_info=True
                )
