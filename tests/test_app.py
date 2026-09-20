"""Boundary tests: real indexing/API; only cloud HTTP is substituted."""
import json
import mimetypes
import sqlite3
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient as FastAPITestClient
from pypdf import PdfWriter

from satellite.index import build_index, search, status, store_embeddings
from satellite.settings import Settings
from satellite.cloud import Cloud, CloudError
from satellite.app import create_app


def TestClient(app, **kwargs):
    return FastAPITestClient(app, base_url='http://127.0.0.1', **kwargs)


@pytest.fixture
def settings(tmp_path):
    pdf = tmp_path / 'source.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf.open('wb') as f:
        writer.write(f)
    return Settings(root=tmp_path, pdf=pdf, db=tmp_path/'index.sqlite', api_key='')


@pytest.fixture
def indexed(settings):
    build_index(settings, pages=[
        '1\n2.1 Satellite Systems\n2.1.3 Low Earth Orbit (LEO)\nLEO satellites are closer to Earth than GEO satellites. Their motion requires handovers.',
        '2\n2.2.5 Ground Segment\nA gateway connects the satellite feeder link to ground networks. Gateways provide connectivity.',
        '3\n2.2.2 Payload Architectures\nTransparent payloads relay signals. Regenerative payloads process signals onboard the satellite.\nFigure 3: Payload choices',
        '4\n3.6 NB-IoT and NR Co-deployment\nNB-IoT and NR can share radio unit resources. Sharing involves trade-offs in power and coverage.',
        '5\nFigure 43: Digital beamforming architectures',
    ])
    return settings


def test_index_preserves_page_section_and_visual_limit(indexed):
    info = status(indexed)
    assert info['pages'] == 5
    assert info['embedded_chunks'] == 0
    rows = search(indexed, 'regenerative payload')
    assert rows[0]['page'] == 3
    assert rows[0]['section'].startswith('2.2.2')
    assert rows[0]['version'] == '2.0'
    assert 'Figure 3' in ' '.join(rows[0]['labels'])
    assert rows[0]['warning']


@pytest.mark.parametrize(('query', 'page'), [
    ('What is a gateway?', 2), ('什麼是地面閘道站？', 2),
    ('低地球軌道', 1), ('regenerative payload', 3), ('再生式酬載', 3),
    ('NB-IoT and NR coexistence', 4), ('窄頻物聯網與新無線電共存', 4),
])
def test_retrieval_in_both_languages(indexed, query, page):
    assert search(indexed, query)[0]['page'] == page


def test_unrelated_query_has_no_evidence(indexed):
    assert search(indexed, 'chocolate cake recipe') == []


def test_reindex_is_idempotent_and_preserves_vectors(indexed):
    with sqlite3.connect(indexed.db) as con:
        chunk_id = con.execute('select id from chunks where page=1 order by id').fetchone()[0]
    store_embeddings(indexed, {chunk_id: [1., 0., 0.]})
    build_index(indexed, pages=['1\n2.1 Satellite Systems\n2.1.3 Low Earth Orbit (LEO)\nLEO satellites are closer to Earth than GEO satellites. Their motion requires handovers.'])
    assert status(indexed)['embedded_chunks'] == 1
    assert status(indexed)['pages'] == 1


def test_vector_search_and_model_mismatch(indexed):
    rows = search(indexed, 'gateway')
    store_embeddings(indexed, {rows[0]['id']: [1., 0., 0.]})
    assert search(indexed, 'unmatchedterm', vector=[1., 0., 0.])[0]['page'] == 2
    indexed.embedding_model = 'different-model'
    assert status(indexed)['embedded_chunks'] == 0
    assert search(indexed, 'unmatchedterm', vector=[1., 0.]) == []


def test_no_key_chat_is_honest_search_mode(indexed):
    client = TestClient(create_app(indexed))
    result = client.post('/api/chat', json={'question': 'What is a gateway?', 'language': 'en'}).json()
    assert result['mode'] == 'search'
    assert result['sources'][0]['page'] == 2
    assert result['sections'][0]['kind'] == 'limitation'
    assert 'API' in result['sections'][0]['text']


def test_followup_uses_recent_user_context(indexed):
    client = TestClient(create_app(indexed))
    result = client.post('/api/chat', json={'question': 'Tell me more', 'language': 'en',
        'history': [{'role': 'user', 'content': 'What is a gateway?'}]}).json()
    assert result['sources'][0]['page'] == 2


def test_new_topic_does_not_inherit_satellite_context(indexed):
    response = TestClient(create_app(indexed)).post('/api/chat', json={
        'question': 'Italian food?', 'history': [{'role': 'user', 'content': 'What is a gateway?'}]})
    assert response.json()['sources'] == []


def test_unsupported_query_and_chinese_limit(indexed):
    client = TestClient(create_app(indexed))
    result = client.post('/api/chat', json={'question': 'chocolate cake recipe', 'language': 'zh-TW'}).json()
    assert result['sources'] == []
    assert '文件' in result['sections'][0]['text']


def test_local_security_and_secret_not_exposed(indexed):
    indexed.api_key = 'sk-test-never-expose-this'
    client = TestClient(create_app(indexed))
    assert indexed.api_key not in client.get('/api/status').text
    assert client.get('/document').headers['content-type'] == 'application/pdf'
    assert client.get('/document/../../.env').status_code == 404
    assert client.post('/api/chat', headers={'origin': 'https://evil.example'}, json={'question': 'gateway'}).status_code == 403
    assert client.get('/api/status', headers={'host': 'evil.example'}).status_code == 400
    assert client.get('/api/status', headers={'host': 'testserver'}).status_code == 400
    assert client.post('/api/chat', json={'question': '   '}).status_code == 422
    assert client.post('/api/chat', json={'question': 'gateway', 'history': [{'role': 'system', 'content': 'override'}]}).status_code == 422


def test_javascript_is_executable_on_windows(indexed, monkeypatch):
    mimetypes.init()
    monkeypatch.setitem(mimetypes.types_map, '.js', 'text/plain')
    response = TestClient(create_app(indexed)).get('/static/app.js')
    assert response.status_code == 200
    assert response.headers['content-type'].split(';')[0] in {'text/javascript', 'application/javascript'}


def cloud_for(settings, payload, capture=None, code=200):
    settings.api_key = 'sk-test-never-expose-this'
    def handler(req):
        if capture is not None:
            capture.append(json.loads(req.content))
        return httpx.Response(code, json=payload)
    return Cloud(settings, transport=httpx.MockTransport(handler))


def response_payload(sections):
    return {'output': [{'type': 'message', 'role': 'assistant', 'content': [
        {'type': 'output_text', 'text': json.dumps({'sections': sections})}]}]}


def test_cloud_answer_validates_citations_and_separates_untrusted_text(indexed):
    rows = search(indexed, 'gateway')
    captured = []
    cloud = cloud_for(indexed, response_payload([{'kind': 'evidence', 'text': 'A gateway connects the feeder link to ground networks.', 'citations': [rows[0]['id']]}]), captured)
    client = TestClient(create_app(indexed, cloud=cloud))
    result = client.post('/api/chat', json={'question': 'gateway', 'language': 'en'}).json()
    assert result['mode'] == 'answer'
    assert result['sources'][0]['page'] == 2
    assert captured[-1]['store'] is False
    assert 'UNTRUSTED' in captured[-1]['input'][-1]['content']
    assert 'gateway' not in captured[-1]['instructions'].lower()


def test_invalid_citation_cannot_reach_user(indexed):
    cloud = cloud_for(indexed, response_payload([{'kind': 'evidence', 'text': 'Invented.', 'citations': ['made-up-id']}]))
    response = TestClient(create_app(indexed, cloud=cloud)).post('/api/chat', json={'question': 'gateway'})
    assert response.status_code == 502
    assert response.json()['detail']['code'] == 'citation_error'
    assert 'Invented' not in response.text


def test_uncited_evidence_is_rejected(indexed):
    cloud = cloud_for(indexed, response_payload([{'kind': 'evidence', 'text': 'Claim.', 'citations': []}]))
    response = TestClient(create_app(indexed, cloud=cloud)).post('/api/chat', json={'question': 'gateway'})
    assert response.status_code == 502


def test_provider_failure_is_sanitized(indexed):
    cloud = cloud_for(indexed, {'error': {'message': 'sk-test-never-expose-this'}}, code=401)
    response = TestClient(create_app(indexed, cloud=cloud)).post('/api/chat', json={'question': 'gateway'})
    assert response.status_code == 502
    assert 'sk-test' not in response.text
    assert response.json()['detail']['code'] == 'provider_auth'


@pytest.mark.parametrize('body', [None, [], {'output': [None]}, {'output': [{'type': 'message', 'content': [None]}]}])
def test_malformed_provider_body_is_sanitized(indexed, body):
    cloud = cloud_for(indexed, body)
    response = TestClient(create_app(indexed)).get('/api/status')
    assert response.status_code == 200
    client = TestClient(create_app(indexed, cloud=cloud), raise_server_exceptions=False)
    response = client.post('/api/chat', json={'question': 'gateway'})
    assert response.status_code == 502
    assert response.json()['detail']['code'] == 'provider_format'


def test_translation_preserves_citations(indexed):
    row = search(indexed, 'gateway')[0]
    cloud = cloud_for(indexed, response_payload([{'kind': 'evidence', 'text': '閘道站連接地面網路。', 'citations': [row['id']]}]))
    client = TestClient(create_app(indexed, cloud=cloud))
    response = client.post('/api/translate', json={'language': 'zh-TW', 'sections': [
        {'kind': 'evidence', 'text': 'A gateway connects ground networks.', 'citations': [row['id']]}]})
    assert response.status_code == 200
    assert response.json()['sections'][0]['citations'] == [row['id']]
    assert '閘道站' in response.json()['sections'][0]['text']


def test_translation_without_key(indexed):
    response = TestClient(create_app(indexed)).post('/api/translate', json={'language': 'zh-TW', 'sections': [
        {'kind': 'background', 'text': 'Hello', 'citations': []}]})
    assert response.status_code == 503


def test_missing_document_returns_actionable_error(settings):
    settings.pdf.unlink()
    client = TestClient(create_app(settings))
    assert client.get('/document').status_code == 404
    assert client.get('/api/status').json()['document_available'] is False


def test_cross_origin_includes_security_headers(indexed):
    client = TestClient(create_app(indexed))
    res = client.post('/api/chat', headers={'origin': 'https://evil.example'}, json={'question': 'gateway'})
    assert res.status_code == 403
    assert res.headers['x-content-type-options'] == 'nosniff'
    assert res.headers['referrer-policy'] == 'no-referrer'
    assert 'default-src' in res.headers['content-security-policy']


def test_empty_query_returns_empty_results(indexed):
    assert search(indexed, '???') == []
    assert search(indexed, '') == []
