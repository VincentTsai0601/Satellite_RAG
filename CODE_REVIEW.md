# Code review — 2026-09-21

**APPROVE — two confirmed blocking defects repaired and regression-tested.**

Target: the current project, including backend, retrieval/indexing, runtime prompt, UI, launch/setup scripts, tests, and documentation. The working tree was clean before review. This report supersedes the earlier assertion that all issues were resolved. No commit, push, publication, or paid API request was performed.

## Findings and revisions

1. **Major, fixed — missing tutor instructions failed open.** `satellite/cloud.py:get_tutor_prompt` swallowed filesystem errors and returned empty or stale cached instructions. Blank files were accepted; invalid UTF-8 caused an unhandled error. It now reads the small security-critical file per answer and rejects missing, unreadable, invalid, or blank instructions with sanitized HTTP 503 / `missing_prompt`. English and Traditional Chinese recovery messages were added. Tests verify that no answer request reaches the provider in these cases.
2. **Major, fixed — malformed Origin crashed POST middleware.** `satellite/app.py:local_only` passed untrusted Origin values to `urlsplit`; `http://[` produced HTTP 500. URLs containing paths or queries were accepted as origins. Exact comparison with the local HTTP origin now rejects malformed values with HTTP 403 and security headers. Normal browser requests passed the smoke test.

## Remaining observations

- **Minor, high confidence:** application shutdown and ingestion do not explicitly call `Cloud.close()`. Process exit releases sockets, but lifecycle cleanup would improve repeated in-process app use.
- **Minor, high confidence:** `renderStatus()` substitutes 97 when the index reports zero pages, obscuring whether page metadata was observed. The current document is verified as 97 pages.
- **Minor, high confidence:** below 600px the hidden sidebar also hides the learning path and New conversation control. The composer and sources remain usable.
- **Recommendation:** expand focused tests for embedding failures, oversized streamed bodies, and translation structure changes.
- Two existing dependency deprecations remain in the Starlette test client (httpx and AnyIO); a dependency migration was outside these fixes.

## Contract and trust review

AGENTS.md is the supplied product contract. No root spec.md or Plans.md was present in the inspected project, so their alignment checks are not applicable. The app retains local-only binding, fixed provider origin, untrusted source/history separation, retrieved citation ID checks, textContent rendering, and explicit opt-in embedding. No accounts, uploads, browsing, or persistent conversations were added.

Citation ID checks establish provenance, not semantic entailment. The runtime prompt requires claim support, source-version qualifiers, and disclosure of the page 39 unit conflict. No live evaluation of generated claims was performed; these controls do not guarantee factual correctness.

Manual review passes covered contract/trust boundaries, regression behavior, and skeptical failure-path inspection. No subagents or external reviewers were used. Static searches found no matching TODO/FIXME, placeholder-data, innerHTML, localStorage, or skipped-test markers in satellite/, static/, and tests/. This was not a dependency vulnerability audit. Harness helper scripts and AST/LSP services were not configured; direct source inspection and searches were used. No TypeScript changed.

Rejected conclusions: localhost use is intentional; injected provider/UI fixtures are explicitly labeled test boundaries, not fabricated live results; valid citations alone do not prove claim accuracy.

## Evidence and verdict

47 tests passed, JavaScript syntax passed, the PDF fingerprint/coverage/database integrity check passed (97 pages, 205 chunks), and the Edge browser smoke test passed. Nine regression cases were added; eight failed before repair and one existing rejection case already passed. See VERIFICATION.md for commands, environment failures, warnings, and limits. Release preflight is not applicable: no release was requested.

```json
{
  "schema_version": "review-result.v1",
  "verdict": "APPROVE",
  "decision_needed": {"required": false},
  "accepted_findings": ["Missing tutor prompt failed open: fixed", "Malformed Origin handling: fixed"],
  "rejected_findings": ["Intentional localhost use is not a defect", "Labeled test fixtures are not live-result claims"],
  "acceptance_bar": {
    "critical_major_zero": true,
    "spec_alignment": "not_applicable",
    "plans_alignment": "not_applicable",
    "regression_safety": "pass",
    "verification_evidence": "pass"
  },
  "team_debate": {"required": true, "mode": "manual-pass", "team_agent_mode": "manual-pass", "agents": [], "disagreements": []},
  "critical_issues": [],
  "major_issues": [],
  "observations": ["HTTP client lifecycle cleanup", "Page-count fallback", "Hidden mobile sidebar controls", "Dependency deprecations"],
  "recommendations": ["Expand embedding, streamed-body, and translation mutation tests"]
}
```
