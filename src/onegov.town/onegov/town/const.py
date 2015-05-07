from onegov.town import _

NEWS_PREFIX = 'aktuelles'

#: Contains the messages that differ for each trait (the handling of all traits
#: is the same). New traits need to adapt the same messages as the others.
TRAIT_MESSAGES = {
    'link': dict(
        name=_("Link"),
        new_page_title=_("New Link"),
        new_page_added=_("Added a new link"),
        edit_page_title=_("Edit Link"),
        delete_message=_("The link was deleted"),
        delete_button=_("Delete link"),
        delete_question=_(
            "Do you really want to delete the link \"${title}\"?"),
    ),
    'page': dict(
        name=_("Topic"),
        new_page_title=_("New Topic"),
        new_page_added=_("Added a new topic"),
        edit_page_title=_("Edit Topic"),
        delete_message=_("The topic was deleted"),
        delete_button=_("Delete topic"),
        delete_question=_(
            "Do you really want to delete the topic \"${title}\"?"),
    ),
    'news': dict(
        name=_("News"),
        new_page_title=_("Add News"),
        new_page_added=_("Added news"),
        edit_page_title=_("Edit News"),
        delete_message=_("The news was deleted"),
        delete_button=_("Delete news"),
        delete_question=_(
            "Do you really want to delete the news \"${title}\"?"),
    )
}
