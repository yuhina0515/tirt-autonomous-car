# Opus5.5 medium independent project review — 2026-10-25

## Request and baseline

User explicitly requested Opus5.5 at medium effort to identify existing and potential problems. Review only. Plan: plans/2026-10-25-opus-5-5-review-plan.md. Baseline HEAD e627004a124b9b10723988579ad2e515efbad560, control source434af1d. Worktree clean before plan. No controller/parameter/output mutations, tests, builds, regeneration, uploads, hardware actions or external account messages.

## Actual execution and tool/version failure

- Global Claude Code2.1.268 exact-model invocation failed API400: model requires CLI2.1.280 or later; no reviewer tools ran. Did not substitute another model.
- Installed exact official npm@anthropic-ai/claude-code2.1.280 plus native win32-x64 dependency under ignored build-output/opus-5-5-review/runtime with install scripts disabled. Executed that isolated binary, global CLI/config unchanged.
- Actual canonical/modelUsage/reported model: claude-opus-5-5. Explicit CLI --effort medium (result does not independently echo effort). Success exit0, is_error false,355.34seconds. Read-only tools used: Read,Glob,Grep; no permission denials; all absolute reads observed within project. No fallback model.
- --safe-mode, --tools and --allowedTools limited to readers, plan permission mode, empty strict MCP config, disabled slash commands, no session persistence. Prompt via stdin;600second bound. Full transport stays ignored, never published. No account credentials in delivered metadata.

## Reports and verified findings

- Verbatim model report: docs/audits/2026-10-25-opus-5-5-medium.zh-TW.md (raw report hash in metadata).
- Separate lead verification: docs/audits/2026-10-25-opus-5-5-medium-verification.zh-TW.md.
- Sanitized execution/model/hash evidence: docs/audits/2026-10-25-opus-5-5-medium.metadata.json.
- Confirms prior stale-candidate BUG. Confirms capture-before-direction-override order bug but disputes its high priority; preserves independent dissent.
- New confirmed implementation bug: after capture has corrected to opposite side, loss fallback selects old turnDirection instead of last turnCaptureSide (rewrite254-259, live car.ino378-386). Right turn, first dropout, F8 capture20/100, second dropout after60ms switches fallback to right45/15 without outer evidence.
- High-priority policy risks: unsupported-source150ms can fault visible F2/F8 or convertF0 to crawling; continued wide recovery100/100 lacks a local event limit. Corrected wording: global180s upper limit still exists, so not literally infinite operation.
- Additional policy gaps:250ms center-memory admission versus120ms wide actuation lifetime; gap-to-wide direction not passed; short side dwell can miss qualification. These need contracts/evidence, not blindly shorter timers.
- Confirms diagnostic/dead-code/comment drift. No proven exporter mismatch, memory overflow, reversed motors or actual sensor polarity. Some risks overlap previous squad and are not wholly new findings.

## Verification and delivery boundary

Explicitly checked requested/actual model match, successful result, tools and permission-denial list, primary source and generated line anchors, and original controller hashes before/after review. Raw report is unmodified. No code fixes applied. Source consistency is not flashed firmware proof. Native compile/resource and vehicle acceptance remain unavailable.

Task-scoped audit artifacts committed/pushed on existing branch and PR6 updated. Prior snapshot tag/formal Release unchanged. Local self-driving_car receives report copies and README links only. Global CLI remains2.1.268; isolated runtime retained in ignored build-output for reproducibility.
