def lchop(text, beginning):
    """ Removes the beginning from the text if the text starts with it. """

    if text.startswith(beginning):
        return text[len(beginning):]

    return text


def rchop(text, end):
    """ Removes the end from the text if the text ends with it. """

    if text.endswith(end):
        return text[:len(end)]

    return text
