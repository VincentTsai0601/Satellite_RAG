"""Page-preserving local retrieval. No API calls are made by this module."""
from collections import Counter
import hashlib
import json
import re
import sqlite3
import unicodedata

import numpy as np
from pypdf import PdfReader

TITLE = 'MSS Reference Architecture'
VERSION = '2.0'
HEADING = re.compile(r'^([1-5](?:\.\d+){0,4})\s{1,}([A-Z][^\n]{3,115})$')
STOP = set('a an and are as at be by can could do does for from have how i in into is it its me more of on or our please should tell than that the their them these they this to us was we what when where which who why will with would you your explain about compare difference differences between learn simple beginner'.split())
ALIASES = {
    '低地球軌道': 'LEO low earth orbit', '低軌': 'LEO', '中地球軌道': 'MEO medium earth orbit',
    '中軌': 'MEO', '地球同步': 'GEO geostationary', '地球靜止': 'GEO geostationary',
    '軌道': 'orbit', '衛星': 'satellite', '地面閘道站': 'gateway', '閘道站': 'gateway',
    '閘道': 'gateway', '地面站': 'gateway ground', '地面段': 'ground segment',
    '太空段': 'space segment', '用戶段': 'user segment', '使用者段': 'user segment',
    '再生式': 'regenerative', '再生型': 'regenerative', '透明式': 'transparent',
    '透明型': 'transparent', '酬載': 'payload', '載荷': 'payload', '負載': 'payload',
    '窄頻物聯網': 'NB-IoT', '新無線電': 'NR', '共存': 'coexistence co-deployment',
    '共同部署': 'co-deployment', '波束跳躍': 'beam hopping', '跳波束': 'beam hopping',
    '波束': 'beam', '資源管理': 'resource management', '漫遊': 'roaming',
    '換手': 'handover', '切換': 'handover', '核心網路': 'core network',
    '核心網': 'core network', '非地面網路': 'NTN', '非地面網絡': 'NTN',
    '無線接取網路': 'RAN', '使用者設備': 'UE', '終端': 'terminal',
    '服務鏈路': 'service link', '饋電鏈路': 'feeder link', '星間鏈路': 'inter satellite links ISL',
    '時延': 'latency', '延遲': 'latency', '都卜勒': 'Doppler', '都普勒': 'Doppler',
    '圖': 'figure', '表格': 'table',
}


def normalize(text):
    return unicodedata.normalize('NFKC', text).translate(str.maketrans({'‑': '-', '–': '-', '−': '-'}))


def query_terms(query):
    expanded = normalize(query)
    for term, english in ALIASES.items():
        if term in expanded:
            expanded += ' ' + english
    return list(dict.fromkeys(t.lower() for t in re.findall(r'[a-zA-Z0-9]+', expanded)
                             if t.lower() not in STOP and len(t) > 1))[:60]


def connect(settings):
    con = sqlite3.connect(settings.db, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def init_schema(con):
    con.executescript('''
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY, page INTEGER NOT NULL, section TEXT NOT NULL,
            text TEXT NOT NULL, labels TEXT NOT NULL, warning TEXT NOT NULL,
            version TEXT NOT NULL, content_hash TEXT NOT NULL,
            embedding TEXT, embedding_model TEXT
        );
        DROP TABLE IF EXISTS chunks_fts;
        CREATE VIRTUAL TABLE chunks_fts USING fts5(id UNINDEXED, section, text, tokenize='porter unicode61');
    ''')


def split_text(text, size=2000, overlap=220):
    """Prefer paragraph/sentence boundaries; never cross a PDF page or section."""
    if len(text) <= size:
        return [text]
    result, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cuts = [text.rfind('\n', start + size // 2, end), text.rfind('. ', start + size // 2, end)]
            cut = max(cuts)
            if cut > start:
                end = cut + 1
        result.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return [part for part in result if part]


def build_index(settings, pages=None):
    if pages is None:
        reader = PdfReader(settings.pdf)
        pages = [page.extract_text() or '' for page in reader.pages]
    settings.db.parent.mkdir(parents=True, exist_ok=True)
    records, report = [], []
    section = 'Front matter'
    for number, raw in enumerate(pages, 1):
        text = normalize(raw)
        lines = [line.rstrip() for line in text.splitlines() if line.strip() != str(number)]
        text = '\n'.join(lines).strip()
        labels = re.findall(r'(?:Figure|Table)\s+\d+\s*:[^\n]*', text)
        warning_parts = []
        if any(label.startswith('Figure') for label in labels):
            warning_parts.append('figure')
        if any(label.startswith('Table') for label in labels):
            warning_parts.append('table')
        if len(text) < 150:
            warning_parts.append('sparse_text')
        # Specific, visually verified source discrepancy; preserve the original values.
        if number == 39 and 'EIRP' in text:
            warning_parts.append('unit_conflict')
        warning = ','.join(warning_parts)
        # Keep tables intact to avoid separating headers, units, and footnotes.
        blocks = []
        if 'table' in warning_parts:
            found = [m for line in lines if (m := HEADING.match(line.strip()))]
            blocks.append((section, text))
            if found:
                section = found[-1].group(0)
        else:
            buf = []
            for line in lines:
                match = HEADING.match(line.strip())
                # Exclude TOC dotted leaders from section inference.
                if match and not re.search(r'\.\s*\.\s*\.', line):
                    if buf:
                        blocks.append((section, '\n'.join(buf)))
                    section = match.group(0)
                    buf = [line]
                else:
                    buf.append(line)
            if buf:
                blocks.append((section, '\n'.join(buf)))
        count = 0
        for heading, block in blocks:
            for part in split_text(block, size=6500 if 'table' in warning_parts else 2000):
                digest = hashlib.sha256(f'{VERSION}|{number}|{heading}|{part}'.encode()).hexdigest()
                records.append((digest[:16], number, heading, part, json.dumps(labels), warning, VERSION, digest))
                count += 1
        report.append({'page': number, 'characters': len(text), 'chunks': count, 'labels': labels, 'warnings': warning_parts})
    with connect(settings) as con:
        init_schema(con)
        old = {row['id']: (row['embedding'], row['embedding_model']) for row in con.execute('SELECT id,embedding,embedding_model FROM chunks')}
        con.execute('DELETE FROM chunks')
        con.execute('DELETE FROM chunks_fts')
        for record in records:
            embedding, model = old.get(record[0], (None, None))
            con.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?,?)', (*record, embedding, model))
            con.execute('INSERT INTO chunks_fts VALUES (?,?,?)', (record[0], record[2], record[3]))
        metadata = {'pages': len(pages), 'title': TITLE, 'version': VERSION,
                    'pdf_sha256': hashlib.sha256(settings.pdf.read_bytes()).hexdigest() if settings.pdf.exists() else '',
                    'extraction_report': report}
        con.executemany('INSERT OR REPLACE INTO metadata VALUES (?,?)', [(key, json.dumps(value)) for key, value in metadata.items()])
    return {'pages': len(pages), 'chunks': len(records), 'report': report}


def status(settings):
    result = {'pages': 0, 'chunks': 0, 'embedded_chunks': 0, 'version': VERSION, 'title': TITLE,
              'document_available': settings.pdf.is_file(), 'api_configured': bool(settings.api_key),
              'chat_model': settings.chat_model, 'embedding_model': settings.embedding_model}
    if not settings.db.exists():
        return result
    with connect(settings) as con:
        result['chunks'] = con.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
        result['embedded_chunks'] = con.execute('SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL AND embedding_model=?', (settings.embedding_model,)).fetchone()[0]
        row = con.execute("SELECT value FROM metadata WHERE key='pages'").fetchone()
        result['pages'] = json.loads(row[0]) if row else 0
    return result


def get_chunks(settings, ids=None):
    if not settings.db.exists():
        return []
    with connect(settings) as con:
        if ids is None:
            rows = con.execute('SELECT * FROM chunks ORDER BY page, rowid').fetchall()
        elif not ids:
            return []
        else:
            rows = con.execute('SELECT * FROM chunks WHERE id IN (' + ','.join('?' for _ in ids) + ')', list(ids)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item['labels'] = json.loads(item['labels'])
        result.append(item)
    return result


def store_embeddings(settings, vectors):
    with connect(settings) as con:
        for chunk_id, vector in vectors.items():
            values = np.asarray(vector, dtype=float)
            if values.ndim != 1 or not values.size or not np.isfinite(values).all() or not np.linalg.norm(values):
                raise ValueError('Invalid embedding vector')
            con.execute('UPDATE chunks SET embedding=?, embedding_model=? WHERE id=?',
                        (json.dumps(values.tolist()), settings.embedding_model, chunk_id))


def search(settings, query, vector=None, limit=6):
    if not settings.db.exists():
        return []
    terms = query_terms(query)
    if not terms and vector is None:
        return []
    scores = {}
    # FTS BM25 supports exact acronyms; token input is normalized and parameterized.
    if terms:
        expression = ' OR '.join('"' + term + '"' for term in terms)
        with connect(settings) as con:
            rows = con.execute('SELECT id, bm25(chunks_fts,0,3,1) AS rank FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT 40', (expression,)).fetchall()
        for rank, row in enumerate(rows):
            scores[row['id']] = 1 / (30 + rank)
    if vector is not None:
        query_vector = np.asarray(vector, dtype=float)
        if query_vector.ndim == 1 and np.isfinite(query_vector).all():
            query_norm = float(np.linalg.norm(query_vector))
            if query_norm > 0:
                with connect(settings) as con:
                    v_rows = con.execute('SELECT id, embedding FROM chunks WHERE embedding IS NOT NULL AND embedding_model=?',
                                        (settings.embedding_model,)).fetchall()
                similar = []
                for row in v_rows:
                    candidate = np.asarray(json.loads(row['embedding']), dtype=float)
                    if candidate.shape == query_vector.shape and np.isfinite(candidate).all():
                        cand_norm = float(np.linalg.norm(candidate))
                        if cand_norm > 0:
                            similarity = float(np.dot(query_vector, candidate) / (query_norm * cand_norm))
                            if similarity >= .25:
                                similar.append((row['id'], similarity))
                for rank, (chunk_id, _) in enumerate(sorted(similar, key=lambda row: -row[1])[:40]):
                    scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (30 + rank)
    if not scores:
        return []
    # Fetch only candidate chunks scored by FTS or vector retrieval
    chunks = get_chunks(settings, ids=list(scores.keys()))
    by_id = {chunk['id']: chunk for chunk in chunks}
    # TOC/index material is useful for browsing but poor primary evidence.
    for chunk_id in list(scores.keys()):
        item = by_id.get(chunk_id)
        if not item:
            scores.pop(chunk_id, None)
            continue
        body = item['text']
        if re.search(r'\.\s*\.\s*\.', body):
            scores[chunk_id] *= .1
        if 'glossary' in item['section'].lower() or item['section'].startswith('5 '):
            scores[chunk_id] *= .4
        substantive = '\n'.join(line for line in body.splitlines()
                                if not HEADING.match(line.strip()) and not re.match(r'^(Figure|Table)\s+\d+\s*:', line.strip()))
        if len(substantive.strip()) < 60:
            scores[chunk_id] *= .15
    result, per_page = [], Counter()
    for chunk_id in sorted(scores, key=lambda key: -scores[key]):
        item = by_id.get(chunk_id)
        if not item or per_page[item['page']] >= 2:
            continue
        per_page[item['page']] += 1
        result.append(public_source(item))
        if len(result) >= limit:
            break
    return result


def public_source(chunk):
    return {key: chunk[key] for key in ('id', 'page', 'section', 'text', 'labels', 'warning', 'version')}
