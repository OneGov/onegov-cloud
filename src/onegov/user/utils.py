from furl import furl


def password_reset_url(user, request, url):
    """ Appends the token needed by PasswordResetForm for a password reset.

    :user:
        The user (model).

    :request:
        The request.

    :url:
        The URL which points to the password reset view (which is using the
        PasswordResetForm).

    :return: An URL containg the password reset token.

    """

    token = request.new_url_safe_token({
        'username': user.username,
        'modified': user.modified.isoformat() if user.modified else ''
    })

    return furl(url).add({'token': token}).url
