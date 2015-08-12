import os.path

from mailbox import Maildir, MaildirMessage
from mailthon.postman import Postman


class MaildirTransport(object):
    """ A transport that pretends to be like python's smtplib.SMTP transport,
    but actually just stores files into a maildir.

    """

    def __init__(self, host, port, maildir):
        # host and port exist for mailthon compatibility, they are ignored
        self.maildir = Maildir(maildir, create=True)

        for d in (os.path.join(maildir, d) for d in ('new', 'cur', 'tmp')):
            if not os.path.exists(d):
                os.makedirs(d)

    def sendmail(self, from_addr, to_addrs, message):
        self.maildir.add(MaildirMessage(message))

        return {}

    def noop(self):
        return 250, ""

    def ehlo(self):
        pass

    def quit(self):
        pass


class MaildirPostman(Postman):
    """ A mailthon postman that stores mails to a maildir. """
    transport = MaildirTransport
