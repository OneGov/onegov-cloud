"""
    Send E-Mail through Postmark

    Adapted from repoze.sendmail: https://github.com/repoze/repoze.sendmail

    Usage:
        qp = EmailQueueProcessor(token, email_dir_1, email_dir_2, ..., limit=x)
        qp.send_messages()
"""

import errno
import json
import logging
import os
import pycurl
import stat
import time

from io import BytesIO


log = logging.getLogger('onegov.core')


# The below diagram depicts the operations performed while sending a message.
# This sequence of operations will be performed for each file in the maildir
# on which ``send_message`` is called.
#
# Any error conditions not depected on the diagram will provoke the catch-all
# exception logging of the ``send_message`` method.
#
# In the diagram the "message file" is the file in the directory that contains
# the message and "tmp file" is a hard link to the message file created in
# in the same directory.
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


class MailQueueProcessor:

    def __init__(self, postmark_token, *paths, limit=None):
        self.paths = paths
        self.limit = limit

        # Keep a pycurl object around, to use HTTP keep-alive - though pycurl
        # is much worse in terms of it's API, the performance is *much* better
        # than requests and it supports modern features like HTTP/2 or HTTP/3
        self.url = 'https://api.postmarkapp.com/email/batch'
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.TCP_KEEPALIVE, 1)
        self.curl.setopt(pycurl.URL, self.url)
        self.curl.setopt(pycurl.HTTPHEADER, [
            'Accept:application/json',
            'Content-Type:application/json',
            f'X-Postmark-Server-Token:{postmark_token}'
        ])
        self.curl.setopt(pycurl.POST, 1)

    def split(self, filename):
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

    def message_files(self):
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

        for path in self.paths:
            for f in os.scandir(path):

                if not f.is_file:
                    continue

                # ignore .sending- .rejected-  files
                if f.name.startswith('.'):
                    continue

                files.append(os.path.join(path, f))

        files.sort(key=lambda i: self.split(i)[-1])

        return tuple(files)

    def send(self, payload):
        """ Sends the mail and returns the API response on error.

            On success this returns None.
        """
        code, body = self.send_request(payload)

        if 400 <= code < 600:
            raise RuntimeError(f"{code} calling {self.url}: {body}")

        result = json.loads(body)

        # If we don't get a list we definitely hit an error
        if not isinstance(result, list):
            return result

        # If any list entry contains errors we forward the result
        for index, status in enumerate(result, start=1):
            if status.get('ErrorCode', 0) != 0:
                return result

        return None

    def send_request(self, payload):
        """ Performes the API request using the given payload. """

        body = BytesIO()

        self.curl.setopt(pycurl.WRITEDATA, body)
        self.curl.setopt(pycurl.POSTFIELDS, payload)
        self.curl.perform()

        code = self.curl.getinfo(pycurl.RESPONSE_CODE)

        body.seek(0)
        body = body.read().decode('utf-8')

        return code, body

    def parse(self, filename):
        # NOTE: For now we don't perform any validation, since it would
        #       be pretty expensive for large batches, Postmark will
        #       complain if we send them garbage
        #       But if we ever decide we want to perform some offline
        #       validation anyways, we can do it in here.
        with open(filename, 'r') as f:
            return f.read()

    def send_messages(self):
        sent = 0
        for filename in self.message_files():
            if self.send_message(filename):
                sent += 1

            # NOTE: While we could enforce the queue limit in message_files()
            #       It could potentially lead to the queue not sending any
            #       files at all when enough of them get stuck in a .sending
            #       state. So it is safer to count how many we actually ended
            #       up submitting to the API and enforcing the limit this way.
            if self.limit and sent >= self.limit:
                break

    def send_message(self, filename):
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
                    return False
                # if we get here, the file existed, but was too
                # old, so it was unlinked
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # file does not exist
                    # it looks like someone else removed the tmp
                    # file, that's fine, we'll try to deliver the
                    # message again later
                    return False

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
                return False
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
                return False
            else:
                # Some other error, propogate it
                raise

        # read message file and send contents
        payload = self.parse(filename)
        if payload:
            status = self.send(payload)
            if status is None:
                log.info(f"Mail batch {filename} sent.")
            else:
                # this should cause stderr output, which
                # will write the cronjob output to chat
                log.error(
                    f"Failed sending mail batch {filename} with "
                    f"API response {status}"
                )
                os.link(filename, failed_filename)
        else:
            # this should cause stderr output, which
            # will write the cronjob output to chat
            log.error(
                f"Discarding mail batch {filename} due to invalid payload"
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

        return True
