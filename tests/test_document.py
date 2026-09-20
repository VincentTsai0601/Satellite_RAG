"""Acceptance checks against the actual shipped 97-page source, without cloud calls."""
import pytest
from satellite.index import search, status
from satellite.settings import Settings


@pytest.mark.parametrize('query', ['What is a gateway?', '什麼是閘道站？'])
def test_gateway_explanation_outranks_glossary(query):
    rows = search(Settings(), query)
    assert any(row['page'] in {29, 30} for row in rows[:2])
    assert rows[0]['page'] < 95


@pytest.mark.parametrize(('query','pages'), [
    ('低地球軌道', {15, 16, 17}),
    ('transparent and regenerative payload', {18, 19, 20, 21}),
    ('再生式酬載', {18, 19, 20, 21}),
    ('NR NB-IoT coexistence', {7, 76, 77, 78}),
    ('窄頻物聯網與新無線電共存', {7, 76, 77, 78}),
])
def test_document_topics_retrieve_explanatory_pages(query, pages):
    assert any(row['page'] in pages for row in search(Settings(), query)[:3])


def test_full_document_is_indexed():
    assert status(Settings())['pages'] == 97
