# Code Review Report - Satellite_RAG (`satellite-learning`)

**Review Date:** 2026-09-21  
**Target:** `Satellite_RAG/satellite-learning`  
**Focus:** Retrieval-Augmented Generation (RAG) pipeline, SQLite/FTS5 indexing, OpenAI cloud integration, FastAPI security middleware, and web interface.

---

## Executive Summary

The codebase is well-structured, follows security-first local architecture principles (localhost binding, prompt injection containment, strict citation validation, no credential leakage), and adheres to the specifications laid out in `AGENTS.md`. 

This code review identified key performance bottlenecks, edge case vulnerabilities, and missing configuration files across the review checklist dimensions (**Correctness**, **Edge Cases**, **Style**, and **Performance**). All identified issues were subsequently resolved and optimized.

---

## Checklist Findings & Optimizations

### 1. Performance & Efficiency

#### Finding 1.1: Redundant Full Table Scans & Deserialization on Every Search
- **Location:** [`satellite/index.py`](satellite/index.py)
- **Problem:**
  - `search()` executed `chunks = get_chunks(settings)` at entry, pulling all table rows including the large `embedding TEXT` column (~10 KB per chunk across 200+ chunks = ~2 MB of JSON) even for keyword-only queries (`vector is None`), which is the default operating mode.
  - Queries with zero alphanumeric terms still queried the entire SQLite table and built a dictionary mapping before returning `[]`.
- **Optimization:**
  - Added an early return if both `terms` and `vector` are empty.
  - Defer chunk loading until after candidate scoring: retrieve only the scored candidate IDs (`ids=list(scores.keys())`, at most 40 chunks) from SQLite.
  - Dramatic reduction in memory allocations and SQLite I/O per query.

#### Finding 1.2: Loop-Level Recomputation in Vector Similarity
- **Location:** [`satellite/index.py`](satellite/index.py)
- **Problem:**
  - `np.linalg.norm(query_vector)` was recalculated inside the chunk evaluation loop on every single iteration (200+ times per search).
  - Evaluated non-matching embedding models in Python rather than filtering at the database layer.
- **Optimization:**
  - Precalculated `query_norm` once outside the loop.
  - Filtered at the SQL layer with `WHERE embedding IS NOT NULL AND embedding_model=?`.

#### Finding 1.3: Ephemeral HTTP Client Overhead
- **Location:** [`satellite/cloud.py`](satellite/cloud.py)
- **Problem:**
  - `Cloud.post()` spawned and destroyed a new `httpx.Client()` context on every API call. During batch ingestion (`--embed`) and consecutive chat/translation requests, this forced repeated TCP handshakes and TLS 1.3 negotiations.
- **Optimization:**
  - Implemented persistent client reuse in `Cloud` (`_get_client()`, `close()`), enabling HTTP keep-alive connection pooling. Preserved injected `transport` compatibility for unit and mock tests.

#### Finding 1.4: Repeated Filesystem I/O for Static Prompt
- **Location:** [`satellite/cloud.py`](satellite/cloud.py)
- **Problem:**
  - `PROMPT.read_text(encoding='utf-8')` was read synchronously from disk on every chat interaction.
- **Optimization:**
  - Implemented cached prompt retrieval with modification time (`st_mtime`) tracking to automatically pick up edits without incurring disk I/O on every request.

---

### 2. Correctness & Security

#### Finding 2.1: Missing Security Headers on Middleware Early Rejections
- **Location:** [`satellite/app.py`](satellite/app.py)
- **Problem:**
  - Early rejection responses in `local_only` middleware (403 for cross-origin and 413 for payload size violations) returned `JSONResponse` directly, bypassing the attachment of security headers (`X-Content-Type-Options`, `Referrer-Policy`, `Cache-Control`, `Content-Security-Policy`).
- **Optimization:**
  - Defined centralized `SECURITY_HEADERS` and applied them consistently across all responses, including early error returns and `CloudError` exception handlers.

#### Finding 2.2: Missing `.env.example` and `.gitignore`
- **Location:** Project root (`satellite-learning/`)
- **Problem:**
  - `README.md`, `index.html`, and `app.js` all instruct users to copy `.env.example` to `.env`, but `.env.example` was missing from the repository.
  - Absence of `.gitignore` created a risk of accidental commits of `.env` containing `OPENAI_API_KEY`, virtual environments, or SQLite database locks.
- **Optimization:**
  - Created `.env.example` with documented environment variables and defaults.
  - Added `.gitignore` ignoring `.env*`, `.venv/`, `__pycache__/`, and SQLite temporary artifacts.

---

### 3. Edge Cases & Reliability

#### Finding 3.1: Incomplete Database Metadata Crashes `ingest --check`
- **Location:** [`satellite/ingest.py`](satellite/ingest.py)
- **Problem:**
  - `con.execute(...).fetchone()[0]` threw an unhandled `TypeError` if `metadata` rows (`pdf_sha256` or `extraction_report`) were missing.
- **Optimization:**
  - Added defensive `None` checks for all query rows in `ingest --check`, returning a clean failure message and exit code `1`.

#### Finding 3.2: Cumulative Source Card Highlighting in UI
- **Location:** [`static/app.js`](static/app.js)
- **Problem:**
  - Clicking multiple citation buttons sequentially left the `.highlight` class active on all previously selected cards.
- **Optimization:**
  - Cleared existing `.source-card.highlight` classes prior to activating a new selection.

#### Finding 3.3: Duplicate Adjacent Citation Badges
- **Location:** [`static/app.js`](static/app.js)
- **Problem:**
  - If a model generated duplicate chunk IDs within a section, duplicate identical citation buttons were rendered side-by-side.
- **Optimization:**
  - Added deduplication via `Set` tracking when rendering citation elements.

#### Finding 3.4: Defensive ID Resolution in `search()`
- **Location:** [`satellite/index.py`](satellite/index.py)
- **Problem:**
  - Direct dictionary subscripting `by_id[chunk_id]` assumed full synchronicity between FTS candidate IDs and chunk table contents.
- **Optimization:**
  - Replaced with `by_id.get(chunk_id)` with safe continuation if an ID is missing.

---

## Verification & Test Additions

The test suite in [`tests/test_app.py`](tests/test_app.py) was updated with regression tests covering:
- Security headers presence on 403 cross-origin rejections.
- Graceful empty result handling for empty/punctuation-only queries.
- Existing tests for citation validation, keyword search, vector retrieval, and prompt boundary protection remain fully compatible.
