from base64 import b64decode


def get_cronjob_by_name(app, name):
    for cronjob in app.config.cronjob_registry.cronjobs.values():
        if name in cronjob.name:
            return cronjob


def get_cronjob_url(cronjob):
    return '/cronjobs/{}'.format(cronjob.id)


def get_mail(outbox, index, encoding='utf-8'):
    message = outbox[index]

    return {
        'from': message['From'],
        'reply_to': message['Reply-To'],
        'subject': message['Subject'],
        'to': message['To'],
        'text': b64decode(
            ''.join(message.get_payload(0).as_string().splitlines()[3:])
        ).decode(encoding),
        'html': b64decode(
            ''.join(message.get_payload(1).as_string().splitlines()[3:])
        ).decode(encoding)
    }
