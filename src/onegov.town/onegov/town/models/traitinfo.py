from onegov.town import _
from onegov.town.elements import DeleteLink, Link, LinkGroup
from onegov.town.models import Clipboard, Editor

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


class TraitInfo(object):
    """" Typically used as a mixin for adjacency list based models,
    this class provides access to the trait related methods.

    Traits are like subtypes of models. For example, the Page model has
    a page trait and a link trait. Both are managed under the same tree as
    the same type (Page), but one is rendered as a redirect, the other as
    a normal page.

    """

    @property
    def trait(self):
        """ Gets the trait of the page. """
        return self.meta.get('trait')

    @trait.setter
    def trait(self, trait):
        """ Sets the trait of the page. """
        self.meta['trait'] = trait

    @property
    def trait_messages(self):
        """ Returns all trait_messages. """
        return TRAIT_MESSAGES

    @property
    def allowed_subtraits(self):
        """ Returns a list of traits that this page may contain. """
        raise NotImplementedError

    @property
    def paste_target(self):
        """ Returns the page that should be used as parent for the content
        pasting if paste is called on the current page (self).

        This is usually just self. If the paste action should put the content
        alongside the current page, it would be the parent.

        """
        raise NotImplementedError

    def is_supported_trait(trait):
        """ Returns true if the given trait is supported by this type This
        doesn't mean that the trait may be added to this page, it serves
        as a simple sanity check, returning True if the combination of the
        type and the trait make any sense at all.

        """
        raise NotImplementedError

    def get_form_class(self, trait):
        """ Returns the form class for the given trait. """
        raise NotImplementedError

    def get_editbar_links(self, request):
        """ Returns the editbar links on the private view of this trait. """
        links = list(self.get_edit_links(request))
        links.append(
            LinkGroup(
                title=_('Add'),
                links=tuple(self.get_add_links(request))
            )
        )

        return links

    def get_add_links(self, request):
        """ Yields the add links shown on the private view of this trait. """

        for trait in self.allowed_subtraits:

            name = self.trait_messages[trait]['name']

            yield Link(
                name,
                request.link(Editor('new', self, trait)),
                classes=(
                    'new-{}'.format(trait),
                    'show-new-content-placeholder'
                )
            )

    def get_edit_links(self, request):
        """ Yields the edit links shown on the private view of this trait. """

        if self.editable:
            yield Link(
                _("Edit"),
                request.link(Editor('edit', self)),
                classes=('edit-link', )
            )
            yield Link(
                _("Copy"),
                request.link(Clipboard.from_url(request, request.path_info)),
                classes=('copy-link', )
            )

        if request.browser_session.has('clipboard_url'):

            yield Link(
                _("Paste"),
                request.link(Editor('paste', self.paste_target)),
                classes=('paste-link', 'show-new-content-placeholder'),
            )

        if self.deletable:

            trait_messages = self.trait_messages[self.trait]
            safe_delete = False if self.children else True

            if safe_delete or request.current_role == 'admin':

                if not safe_delete:
                    extra_warning = _(
                        "Please note that this page has subpages "
                        "which will also be deleted!"
                    )
                else:
                    extra_warning = ""

                yield DeleteLink(
                    _("Delete"), request.link(self),
                    confirm=_(trait_messages['delete_question'], mapping={
                        'title': self.title
                    }),
                    yes_button_text=trait_messages['delete_button'],
                    extra_information=extra_warning,
                    redirect_after=request.link(self.parent)
                )
            else:
                yield DeleteLink(
                    text=_("Delete"),
                    url=request.link(self),
                    confirm=_("This page can't be deleted."),
                    extra_information=_(
                        "This page has subpages. Only administrators can "
                        "delete pages with subpages. To delete this page, "
                        "delete all subpages first or ask an administrator "
                        "to do it for you."
                    )
                )
