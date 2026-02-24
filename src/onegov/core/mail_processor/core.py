from __future__ import annotations

import errno
import logging
import os
import stat
import time


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

    def __init__(self, *paths: str, limit: int | None = None):
        self.paths = paths
        self.limit = limit

    def split(self, filename: str) -> tuple[str, str, str]:
        """ Returns the path, the name and the suffix of the given path. """

        # FIXME: rpartition seems better here, also we should probably
        #        use `os.path.sep` instead of hardcoding `/`
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

        for path in self.paths:
            for f in os.scandir(path):

                if not f.is_file():
                    continue

                # ignore .sending- .rejected-  files
                if f.name.startswith('.'):
                    continue

                # ignore .tmp files created by safe_move
                if f.name.endswith('.tmp'):
                    continue

                files.append(os.path.join(path, f))

        files.sort(key=lambda i: self.split(i)[-1])

        return tuple(files)

    def send(self, filename: str, payload: str) -> bool:
        """ Sends the mail and returns success as bool """
        raise NotImplementedError()

    def parse(self, filename: str) -> str:
        # NOTE: For now we don't perform any validation, since it would
        #       be pretty expensive for large batches, Postmark will
        #       complain if we send them garbage
        #       But if we ever decide we want to perform some offline
        #       validation anyways, we can do it in here.
        with open(filename) as f:
            return f.read()

    def send_messages(self) -> None:
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

    def send_message(self, filename: str) -> bool:
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
            # A status of None means we skipped the message
            # and maybe will try again.
            status = self.send(filename, payload)
            if status is True:
                log.info(f'Mail batch {filename} sent.')
            elif status is False:
                os.link(filename, failed_filename)
        else:
            # this should cause stderr output, which
            # will write the cronjob output to chat
            log.error(
                f'Discarding mail batch {filename} due to invalid payload'
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
