# Opus5.5 medium independent project review — 2026-10-25

## Goal

Run the user's exact requested model against the current TIRT project and identify existing/potential issues. Review only: no controller/parameter changes, tests, builds, export/regeneration, uploads, hardware runs or deployment.

## Baseline

- HEAD e627004a124b9b10723988579ad2e515efbad560; control source remains434af1d. Initial worktree clean.
- Primary files: active root XML/Arduino, tools/rewrite_car.py, tools/export_car.mjs, blockly_codegen.py, hardware and current-state docs. Separate retained temporal candidate from root-car evidence.
- First form independent findings; then compare previous six-department audit rather than treating it as ground truth.

## Model and execution

- Requested model: claude-opus-5-5; effort: medium. Do not substitute aliases or another model.
- Initial local Claude Code2.1.268 call rejected by API400 requiring version2.1.280 or later; it performed no review tools.
- Installed exact official npm package@anthropic-ai/claude-code2.1.280 and platform dependency in ignored build-output/opus-5-5-review/runtime, with install scripts disabled. Execute isolated native binary; global CLI/config unchanged.
- Claude Code flags: --safe-mode, --print, --model claude-opus-5-5, --effort medium, --tools Read,Glob,Grep, matching --allowedTools, --permission-mode plan, --strict-mcp-config with empty server map, --disable-slash-commands, --no-session-persistence, stream-json verbose output.
- CLI receives explicit prompt through stdin. Ten-minute bounded attempt; no fallback model. Raw transport output stays ignored and is not published; only sanitized model metadata and actual completed report may be delivered.
- No external computer/account messages authorized or sent; only requested model API review of project context.

## Acceptance

Verify result success, actual model metadata, no denied required reads, only allowed tool calls, and source/output hashes unchanged. Preserve raw model report without rewriting its findings, separately verify claims and record agreement/disagreement. If the model cannot run, report exact limitation rather than inventing an Opus review. Record original CLI failure and isolated-runtime workaround in English handoff.
