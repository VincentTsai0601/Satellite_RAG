"""Run locally: python -m satellite.ingest [--embed | --check]."""
import argparse
import hashlib
import json
import sys

from .settings import Settings
from .index import build_index, connect, get_chunks, status, store_embeddings
from .cloud import Cloud, CloudError


def main():
    parser = argparse.ArgumentParser(description='Build/check the local MSS index. --embed sends extracted text to OpenAI (billed API).')
    parser.add_argument('--embed', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    settings = Settings.load()
    if args.check:
        info = status(settings)
        print(json.dumps(info, indent=2))
        if not info['document_available'] or not info['chunks']:
            return 1
        with connect(settings) as con:
            sha_row = con.execute("SELECT value FROM metadata WHERE key='pdf_sha256'").fetchone()
            cov_row = con.execute("SELECT value FROM metadata WHERE key='extraction_report'").fetchone()
            integrity_row = con.execute('PRAGMA integrity_check').fetchone()
        if not sha_row or not cov_row or not integrity_row:
            print('Document fingerprint, page coverage, and SQLite integrity: FAILED (missing metadata)')
            return 1
        expected = json.loads(sha_row[0])
        integrity = integrity_row[0]
        coverage = json.loads(cov_row[0])
        valid = (hashlib.sha256(settings.pdf.read_bytes()).hexdigest() == expected and integrity == 'ok'
                 and all(page['chunks'] > 0 for page in coverage))
        print('Document fingerprint, page coverage, and SQLite integrity: ' + ('OK' if valid else 'FAILED'))
        return 0 if valid else 1
    if not settings.pdf.exists():
        print('Missing data/mss-reference-v2.pdf. See README.md.', file=sys.stderr)
        return 1
    result = build_index(settings)
    report = {'source': 'MSS Reference Architecture Version 2.0', 'pages': result['pages'],
              'chunks': result['chunks'], 'page_report': result['report'],
              'note': 'Text-only extraction. Figure arrows, embedded diagram labels and table layout may be missing. Inspect original PDF for visual evidence.'}
    (settings.root / 'data' / 'extraction-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Indexed {result['pages']} pages into {result['chunks']} passages locally.")
    if not args.embed:
        print('Keyword search ready. Embeddings are optional: configure .env, then run python -m satellite.ingest --embed.')
        return 0
    if not settings.api_key:
        print('OPENAI_API_KEY is missing. No text was sent. Configure .env first.', file=sys.stderr)
        return 2
    pending = [chunk for chunk in get_chunks(settings) if not chunk['embedding'] or chunk['embedding_model'] != settings.embedding_model]
    cloud = Cloud(settings)
    try:
        for start in range(0, len(pending), 24):
            batch = pending[start:start + 24]
            vectors = cloud.embed([chunk['section'] + '\n' + chunk['text'] for chunk in batch])
            store_embeddings(settings, {chunk['id']: vector for chunk, vector in zip(batch, vectors)})
            print(f'Embedded {min(start+24,len(pending))}/{len(pending)} pending passages.', flush=True)
    except CloudError as exc:
        print(f'Embedding stopped: {exc.code}. Completed batches are saved; rerun to resume.', file=sys.stderr)
        return 2
    print('Hybrid retrieval is ready. Restart the app if you changed .env.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
