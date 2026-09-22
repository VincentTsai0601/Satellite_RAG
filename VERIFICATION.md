# Verification — 2026-09-21

## Results

- `git diff --check`: passed; Git noted normal LF-to-CRLF normalization for the test file.
- `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache/review-green-20260921`: **47 passed**, two dependency warnings.
- `.\.venv\Scripts\python.exe -m satellite.ingest --check`: **passed**, 97 pages, 205 chunks, zero embedded chunks. Document fingerprint, page coverage, and SQLite integrity OK.
- `node --check static/app.js`: passed.
- `node tests/browser-smoke.cjs`: passed using bundled Playwright and installed Microsoft Edge against http://127.0.0.1:8765.

Browser environment: PLAYWRIGHT_MODULE was set to `C:\Users\Singama\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright`. This is a machine-specific test-tool path, not an application dependency.

The browser test exercised English/Traditional Chinese switching, real no-key retrieval, PDF page-link targets, preservation of original messages, translation/show-original with injected UI fixtures, unsupported queries, reset, mobile overflow checks, and absence of page errors. A backend test fetched the configured PDF. PDF page contents and screen-reader usability were not visually assessed.

## Regression evidence

Before production edits, focused new tests returned **8 failed, 1 passed**, reproducing missing/blank/invalid/deleted tutor prompt handling and malformed Origin handling. After repair the complete suite passed. Provider tests use injected HTTP transport; these are not live OpenAI tests.

## Environment problems and limitations

The initial plain pytest command returned **8 passed, 30 setup errors** because Windows denied access to the existing system pytest temporary directory. An isolated rerun confirmed PermissionError in fixture setup. A fresh project-local --basetemp resolved this without modifying that directory or its permissions. Use a fresh unused directory for future runs; pytest may clear its specified base directory.

Sandbox process and file helpers failed during setup. Approved elevated shell operations were used for inspection, edits, and tests. The in-app browser connector failed to initialize; the existing Playwright test succeeded using the bundled module.

Starlette reported existing deprecations for httpx and the AnyIO BlockingPortal alias. No dependency update was made.

No API key was configured. No live embedding, generated-answer, translation, semantic citation, or adversarial prompt evaluation was performed. No paid API requests or web searches were made. Technical diagrams and every source claim were not independently re-audited against the PDF.
