import morepath

from babel import Locale
from onegov.core.elements import Link, LinkGroup
from onegov.core.security import Private, Public
from onegov.org.models import Editor, Topic
from onegov.org.views.editor import handle_new_page
from onegov.org.views.page import view_topic
from onegov.ilz import _, ILZApp
from onegov.town6.layout import EditorLayout, PageLayout
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.ilz.request import ILZRequest
    from onegov.town6.request import TownRequest
    from webob import Response


@ILZApp.html(model=Topic, template='topic.pt', permission=Public)
def ilz_view_topic(
    self: Topic,
    request: TownRequest
) -> RenderData | Response:
    layout = PageLayout(self, request)
    result = view_topic(self, request, layout)
    if self.locale and len(request.app.locales) > 1:
        if request.is_manager:
            assert isinstance(layout.editbar_links, list)
            layout.editbar_links.insert(-1, LinkGroup(
                title=_('Translations'),
                links=[
                    Link(
                        text=(Locale.parse(locale).get_language_name(
                            request.locale) or locale).capitalize(),
                        url=request.class_link(
                            Editor,
                            {
                                'action': 'new',
                                'trait': 'page',
                                'page_id': self.id,
                            },
                            'translate',
                            query_params={'locale': locale}
                        ),
                        attrs={'class': 'edit-link'}
                    )
                    for locale in sorted(request.app.locales)
                    if locale != self.locale
                ]
            ))
        elif (
            self.locale != request.locale
            and request.locale in self.alt_locale_ids
        ):
            # redirect to the correct language
            topic = request.session.get(
                Topic,
                self.alt_locale_ids[request.locale]
            )
            if topic is not None:
                return morepath.redirect(request.link(topic))

    return result


def get_form_class(model: Editor, request: ILZRequest) -> type[Form]:
    assert model.page is not None
    return model.page.get_form_class('page', 'new', request)


@ILZApp.form(
    model=Editor,
    template='form.pt',
    permission=Private,
    form=get_form_class,
    name='translate'
)
def handle_translate_topic(
    self: Editor,
    request: ILZRequest,
    form: Form
) -> RenderData | Response:

    if self.trait != 'page' or self.action != 'new':
        raise HTTPNotFound()

    topic = self.page
    if not isinstance(topic, Topic):
        raise HTTPNotFound()

    locale = request.GET.get('locale')
    if locale not in request.app.locales or topic.locale is None:
        raise HTTPNotFound()

    # NOTE: If a translation already exists, redirect to it
    if locale in topic.alt_locale_ids:
        return morepath.redirect(request.class_link(
            Editor,
            {
                'action': 'edit',
                'trait': 'page',
                'page_id': topic.alt_locale_ids[locale]
            },
        ))

    def setup_alt_locale_ids(new_topic: Topic) -> None:
        assert topic.locale is not None
        with request.session.no_autoflush:
            # determine the actual parent page we should be using
            parent = topic.parent
            if isinstance(parent, Topic) and locale in parent.alt_locale_ids:
                parent = request.session.get(
                    Topic,
                    parent.alt_locale_ids[locale]
                ) or parent

            new_topic.parent = parent
            new_topic.locale = locale
            # link existing translations to new translation
            new_topic.alt_locale_ids = topic.alt_locale_ids.copy()
            new_topic.alt_locale_ids[topic.locale] = topic.id

            # link new translation to other linked translations
            for topic_id in topic.alt_locale_ids.values():
                existing = request.session.get(Topic, topic_id)
                if existing is None:
                    continue

                alt_locale_ids = existing.alt_locale_ids
                alt_locale_ids[locale] = new_topic.id
                existing.alt_locale_ids = alt_locale_ids

            # link new translation to source translation
            alt_locale_ids = topic.alt_locale_ids
            alt_locale_ids[locale] = new_topic.id
            topic.alt_locale_ids = alt_locale_ids

    language = Locale.parse(locale).get_language_name(request.locale)
    if language is None:
        language = locale
    title = _('Translate to ${language}', mapping={'language': language})
    layout = EditorLayout(self, request, title)
    return handle_new_page(
        self,
        request,
        form,
        src=topic,
        layout=layout,
        added_page_callback=setup_alt_locale_ids
    )
