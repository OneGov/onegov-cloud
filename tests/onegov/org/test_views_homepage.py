from __future__ import annotations

import json
import pytest
import transaction

from onegov.org.views.homepage import _blocknote_constrained_schema
from onegov.org.views.homepage import _blocknote_document_state
from onegov.org.views.homepage import _blocknote_editable_ids
from onegov.org.views.homepage import _blocknote_normalize_operation_targets
from onegov.org.views.homepage import _blocknote_tool_arguments


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_homepage(client: Client) -> None:
    client.app.org.meta['homepage_cover'] = "<b>0xdeadbeef</b>"
    client.app.org.meta['homepage_structure'] = """
        <row>
            <column span="8">
                <homepage-cover />
            </column>
            <column span="4">
                <panel>
                    <news />
                </panel>
                <panel>
                    <events />
                </panel>
            </column>
        </row>
    """

    transaction.commit()

    homepage = client.get('/')

    assert '<b>0xdeadbeef</b>' in homepage
    assert '<h2>Veranstaltungen</h2>' in homepage


def test_blocknote_ai(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client.app.infomaniak_api_token = 'secret-token'
    client.app.infomaniak_product_id = 'product-id'
    request_data: dict[str, Any] = {}

    class UpstreamResponse:
        ok = True
        status_code = 200
        text = ''

        @staticmethod
        def json() -> dict[str, object]:
            return {
                'choices': [{
                    'finish_reason': 'stop',
                    'message': {
                        'content': json.dumps({
                            'operations': [{
                                'type': 'update',
                                'id': 'block-1$',
                                'block': '<p>Verbessert</p>',
                            }],
                        }),
                    },
                }],
            }

    class UpstreamSession:
        def __init__(self, **kwargs: object) -> None:
            request_data['session'] = kwargs

        def __enter__(self) -> UpstreamSession:
            return self

        def __exit__(self, *args: object) -> None:
            pass

        @staticmethod
        def post(**kwargs: Any) -> UpstreamResponse:
            request_data.update(kwargs)
            return UpstreamResponse()

    monkeypatch.setattr(
        'onegov.org.views.homepage.niquests.Session',
        UpstreamSession,
    )
    client.login_admin()
    response = client.post_json(
        f'/blocknote-ai?csrf-token={client.csrf_token}',
        {
            'messages': [{
                'id': 'message-1',
                'role': 'user',
                'metadata': {
                    'documentState': {
                        'selection': False,
                        'isEmptyDocument': False,
                        'blocks': [{
                            'id': 'block-1$',
                            'block': '<p>Text</p>',
                        }],
                    },
                },
                'parts': [{'type': 'text', 'text': 'Verbessere den Text'}],
            }],
            'toolDefinitions': {
                'applyDocumentOperations': {
                    'description': 'Apply document operations',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {'operations': {'type': 'array'}},
                        'required': ['operations'],
                    },
                    'outputSchema': {'type': 'object'},
                },
            },
        },
    )

    assert response.content_type == 'text/event-stream'
    assert response.headers['X-Vercel-AI-UI-Message-Stream'] == 'v1'
    events = [
        json.loads(line.removeprefix('data: '))
        for line in response.text.splitlines()
        if line.startswith('data: {')
    ]
    tool_input = next(
        event for event in events
        if event['type'] == 'tool-input-available'
    )
    assert tool_input['type'] == 'tool-input-available'
    assert tool_input['toolCallId']
    assert tool_input['toolName'] == 'applyDocumentOperations'
    assert tool_input['input'] == {
        'operations': [{
            'type': 'update',
            'id': 'block-1$',
            'block': '<p>Verbessert</p>',
        }],
    }
    assert request_data['headers']['Authorization'] == 'Bearer secret-token'
    assert request_data['session'] == {
        'disable_http2': True,
        'disable_http3': True,
    }
    assert request_data['url'] == (
        'https://api.infomaniak.com/2/ai/product-id'
        '/openai/v1/chat/completions'
    )
    assert request_data['json']['stream'] is False
    assert request_data['json']['response_format'] == {
        'type': 'json_schema',
        'json_schema': {
            'name': 'apply_document_operations',
            'description': 'Apply document operations',
            'schema': {
                'type': 'object',
                'properties': {'operations': {'type': 'array'}},
                'required': ['operations'],
            },
            'strict': True,
        },
    }
    assert request_data['json']['reasoning_effort'] == 'none'
    assert 'tools' not in request_data['json']
    assert 'tool_choice' not in request_data['json']
    assert 'Verbessere den Text' == request_data['json']['messages'][-1][
        'content'
    ]


def test_blocknote_ai_content_tool_fallback() -> None:
    operations = {
        'operations': [{
            'type': 'update',
            'id': 'block-1$',
            'block': '<p>Verbessert</p>',
        }],
    }

    assert _blocknote_tool_arguments(json.dumps(operations)) == operations
    assert _blocknote_tool_arguments(
        f'```json\n{json.dumps(operations)}\n```'
    ) == operations
    assert _blocknote_tool_arguments(
        '<tool_call>' + json.dumps({
            'name': 'applyDocumentOperations',
            'arguments': operations,
        }) + '</tool_call>'
    ) == operations
    assert _blocknote_tool_arguments('Apply these operations now') is None
    assert _blocknote_tool_arguments('{"answer": "no operations"}') is None


def test_blocknote_ai_constrains_and_normalizes_block_ids() -> None:
    state = {
        'selection': True,
        'selectedBlocks': [
            {'id': 'selected-1$', 'block': '<p>One</p>'},
            {'id': 'selected-2$', 'block': '<p>Two</p>'},
        ],
        'blocks': [{'block': '<p>One</p>'}, {'block': '<p>Two</p>'}],
    }
    schema: dict[str, Any] = {
        'type': 'object',
        'properties': {
            'operations': {
                'type': 'array',
                'items': {
                    'anyOf': [{
                        'type': 'object',
                        'properties': {
                            'type': {'enum': ['update']},
                            'id': {'type': 'string'},
                        },
                    }, {
                        'type': 'object',
                        'properties': {
                            'type': {'enum': ['add']},
                            'referenceId': {'type': 'string'},
                        },
                    }],
                },
            },
        },
    }

    constrained: Any = _blocknote_constrained_schema(schema, state)
    variants = constrained['properties']['operations']['items']['anyOf']
    assert variants[0]['properties']['id']['enum'] == [
        'selected-1$',
        'selected-2$',
    ]
    assert variants[1]['properties']['referenceId']['enum'] == [
        'selected-1$',
        'selected-2$',
    ]
    assert 'enum' not in schema['properties']['operations']['items'][
        'anyOf'
    ][0]['properties']['id']

    assert _blocknote_normalize_operation_targets({
        'operations': [{
            'type': 'update',
            'id': 'selected-1',
            'block': '<p>Changed</p>',
        }],
    }, state) == {
        'operations': [{
            'type': 'update',
            'id': 'selected-1$',
            'block': '<p>Changed</p>',
        }],
    }
    assert _blocknote_normalize_operation_targets({
        'operations': [{'type': 'unsupported'}],
    }, state) is None
    assert _blocknote_normalize_operation_targets({
        'operations': [{
            'type': 'update',
            'id': 'invented$',
            'block': '<p>Changed</p>',
        }],
    }, state) is None

    assert _blocknote_normalize_operation_targets({
        'operations': [{
            'type': 'update',
            'id': 'block-2$',
            'block': '<p>Two</p>',
        }],
    }, state) == {
        'operations': [{
            'type': 'update',
            'id': 'selected-2$',
            'block': '<p>Two</p>',
        }],
    }
    assert _blocknote_normalize_operation_targets({
        'operations': [{
            'type': 'update',
            'id': 'invented$',
            'block': '<h2>Two improved</h2>',
        }],
    }, state) == {
        'operations': [{
            'type': 'update',
            'id': 'selected-2$',
            'block': '<h2>Two improved</h2>',
        }],
    }

    single_block_state = {
        'selection': False,
        'blocks': [{'id': 'only-block$', 'block': '<p>One</p>'}],
    }
    assert _blocknote_normalize_operation_targets({
        'operations': [{
            'type': 'update',
            'id': 'invented$',
            'block': '<p>Changed</p>',
        }],
    }, single_block_state) == {
        'operations': [{
            'type': 'update',
            'id': 'only-block$',
            'block': '<p>Changed</p>',
        }],
    }


def test_blocknote_ai_retry_uses_previous_addressable_state() -> None:
    previous = {
        'selection': False,
        'blocks': [{'id': 'existing$', 'block': '<p>Existing</p>'}],
    }
    retry = {
        'selection': True,
        'selectedBlocks': [],
        'blocks': [{'block': '<p>Existing</p>'}],
    }
    assert _blocknote_document_state([{
        'metadata': {'documentState': previous},
    }, {
        'metadata': {'documentState': retry},
    }]) is previous

    current = {
        'selection': False,
        'blocks': [{'id': 'current$', 'block': '<p>Current</p>'}],
    }
    assert _blocknote_document_state([{
        'metadata': {'documentState': previous},
    }, {
        'metadata': {'documentState': current},
    }]) is current

    empty_selection_with_addressable_document = {
        'selection': True,
        'selectedBlocks': [],
        'blocks': [{'id': 'current$', 'block': '<p>Current</p>'}],
    }
    assert _blocknote_editable_ids(
        empty_selection_with_addressable_document
    ) == ['current$']
    assert _blocknote_document_state([{
        'metadata': {
            'documentState': empty_selection_with_addressable_document,
        },
    }]) is empty_selection_with_addressable_document


def test_add_new_root_topic(client: Client) -> None:
    # ensure a root page can be added once admin is logged-in
    client.login_admin().follow()

    page = client.get('/')
    assert 'Hinzufügen' in page
    assert 'Thema' in page

    page = page.click('Thema')
    page.form['title'] = 'Super Org Thema'
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert 'Das neue Thema wurde hinzugefügt' in page
    assert page.pyquery('.callout')
    assert page.pyquery('.success')

    page = client.get('/topics/super-org-thema')
    assert page.status_code == 200
    assert 'Super Org Thema' in page
