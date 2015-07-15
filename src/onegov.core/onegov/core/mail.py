import os.path

from mailbox import Maildir, MaildirMessage
from mailthon.helpers import format_addresses
from mailthon.postman import Postman as BasePostman


# pending issue: https://github.com/eugene-eeo/mailthon/issues/18
class Postman(BasePostman):
    def deliver(self, conn, envelope):
        rejected = conn.sendmail(
            envelope.mail_from,
            envelope.receivers,
            envelope.string(),
        )

        return self.response_cls(conn.noop(), rejected)


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
        msg = MaildirMessage(message)
        # the x-* headers are for repoze.sendmail compatibility
        # (i.e. we can use the qp script if we use these headers)
        msg['X-Actually-From'] = msg['from'] = from_addr
        msg['X-Actually-To'] = msg['to'] = format_addresses(to_addrs)
        self.maildir.add(MaildirMessage(msg))

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
