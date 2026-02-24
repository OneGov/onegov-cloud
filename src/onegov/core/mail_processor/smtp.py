"""
Send E-Mail through SMTP

Adapted from `repoze.sendmail<https://github.com/repoze/repoze.sendmail>`_.

Usage::

    mailer = smptlib.SMTP(host, port)
    qp = SMTPEmailQueueProcessor(mailer, maildir1, maildir2, ..., limit=x)
    qp.send_messages()
"""
from __future__ import annotations

import json
import smtplib

from base64 import b64decode
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate
from email.utils import make_msgid
from .core import log, MailQueueProcessor


class SMTPMailQueueProcessor(MailQueueProcessor):

    def __init__(
        self,
        mailer: smtplib.SMTP,
        *paths: str,
        limit: int | None = None
    ):
        super().__init__(*paths, limit=limit)
        self.mailer = mailer

    def parse_payload(
        self,
        filename: str,
        payload: str
    ) -> list[EmailMessage]:
        try:
            items = json.loads(payload)
            if not isinstance(items, list):
                raise ValueError('Invalid JSON payload')  # noqa: TRY004

            messages: list[EmailMessage] = []
            for item in items:
                message = EmailMessage(policy=SMTP)
                message['from'] = item['From']
                message['to'] = item['To']
                message['date'] = formatdate()

                has_message_id = any(
                    h['Name'].lower() == 'message-id'
                    for h in item.get('Headers', [])
                )
                if not has_message_id:
                    message['message-id'] = make_msgid()

                if 'ReplyTo' in item:
                    message['reply-to'] = item['ReplyTo']
                if 'Cc' in item:
                    message['cc'] = item['Cc']
                if 'Bcc' in item:
                    message['bcc'] = item['Bcc']
                if 'Subject' in item:
                    message['subject'] = item['Subject']
                for header in item.get('Headers', []):
                    message[header['Name'].lower()] = header['Value']

                # set message content
                message.set_content(item['TextBody'])
                if 'HtmlBody' in item:
                    message.add_alternative(
                        item['HtmlBody'],
                        subtype='html'
                    )

                # add attachments
                for attachment in item.get('Attachments', []):
                    # TODO: use add_related for attachment on html part if we
                    #       ever start supporting CID in onegov.core.mail
                    maintype, subtype = attachment['ContentType'].split('/', 1)
                    content: str = attachment['Content']
                    message.add_attachment(
                        # FIXME: This can be optimized with a custom content
                        #        manager that folds the already base64 encoded
                        #        attachment content instead of having to do
                        #        this expensive decode/encode step here.
                        b64decode(content.encode('ascii')),
                        maintype=maintype,
                        subtype=subtype,
                        filename=attachment['Name']
                    )

                messages.append(message)
            return messages
        except (json.JSONDecodeError, ValueError, KeyError):
            log.error(f'Discarding batch {filename} with invalid JSON payload')
            return []

    def send(self, filename: str, payload: str) -> bool:
        """ Sends the mail and returns success as bool """
        messages = self.parse_payload(filename, payload)
        success = len(messages) > 0
        for index, message in enumerate(messages):
            try:
                send_errors = self.mailer.send_message(message)
                if send_errors:
                    # NOTE: Someone will have received the mail, but some of
                    #       the recipients will have failed. We'll treat it as
                    #       success but log the error as a warning.
                    log.warning(
                        f'SMTP send error when sending batch {filename} at '
                        f'index {index}: {send_errors}'
                    )
            except smtplib.SMTPResponseException as e:
                # TODO: If we get only transient errors on the entire
                #       batch it would maybe be nice to have a way of
                #       retrying the batch at a later time automatically
                log.error(
                    f'SMTP error when sending batch {filename} at index '
                    f'{index}: {e.args}'
                )
                success = False

        return success
