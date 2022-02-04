def get_cronjob_by_name(app, name):
    for cronjob in app.config.cronjob_registry.cronjobs.values():
        if name in cronjob.name:
            return cronjob


def get_cronjob_url(cronjob):
    return '/cronjobs/{}'.format(cronjob.id)


def edit_bar_links(page, attrib=None):
    links = page.pyquery('.edit-bar a')
    if attrib:
        if attrib == 'text':
            return [li.text for li in links]
        return [li.attrib[attrib] for li in links]
    return links
