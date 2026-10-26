# Project save and summary — 2026-10-26

## Request and baseline

User requested project data preservation and summary. Initial HEAD7d1d3bf7665da89a1f3d12cab7a97adb02dbb10b, clean worktree. Controller unchanged from434af1d. Branch docs/legacy-sensor-truth-table, PR6 open. Latest formal Release v0.4.0 rechecked through GitHub CLI. No memory-store update requested or performed.

## Actions and decisions

- Add docs/PROJECT_SUMMARY_2026-10-26.zh-TW.md and machine-readable docs/snapshots/2026-10-26-reviewed-state.json; link from README/AGENTS.
- Preserve latest six-department review, exact Opus5.5 medium final report and independent verification. Rechecked raw report SHA256 against saved metadata.
- Clearly mark all three confirmed bugs unresolved; document policy risks and execution/firmware/field evidence gaps. Preserve priority disagreement rather than claiming consensus.
- Create new annotated snapshot/2026-10-26-reviewed-state at this documentation commit, retaining old snapshot and v0.4.0 tag/assets.
- Local archive target: E:/Projects/XiangyiRobotDreamFactory/self-driving_car/snapshots/2026-10-26-7d1d3bf. Full tracked-source ZIP, extracted current source with exact active XML/Arduino bytes, stable-v0.4.0 comparison files, summary/README, snapshot metadata and SHA256SUMS. Do not package ignored runtime, transport/reasoning logs, capture/private files, secrets or proprietary vendor editor.

## Verification and boundary

Active local car.xml/car.ino matched team-repo; controller/generator Git diff from434af1d is empty. Metadata source hashes pin archived main files; verify complete archive manifest after creation. Stable XML/Arduino match Release digests when archived. Existing global Claude CLI/settings are not modified.

No controller fixes, speed/stop policy edits, tests, compilation, regeneration, uploads, hardware runs, merge or new Release. Source state does not identify current flashed firmware. Snapshot is development/audit data, not measured vehicle stability.

## Resume

Read latest summary first. Follow-up implementation should separately address candidate lifetime, capture fallback side, and direction/capture ordering, then decide phase contracts and uncertainty budgets. Respect existing no-extra-tests instruction and current user-selected loss-stop flags until scope changes. Never infer physical white=F0/F14 or source synchronization=hardware acceptance.
