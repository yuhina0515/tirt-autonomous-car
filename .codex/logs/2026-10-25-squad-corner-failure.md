# Squad handoff: corner failure audit (2026-10-25)

## Plan, baseline and scope

- Plan: plans/2026-10-25-corner-failure-plan.md
- Baseline HEAD43ffc1fbb8f16ad750393f13d886401f97891246; control files equal434af1d. Branch docs/legacy-sensor-truth-table, existing PR6. Initial working tree clean.
- Read-only source snapshot outside working tree: C:/Users/Yuhina/Documents/Codex/2026-10-24/tirt/audit-snapshots/2026-10-25-corner-failure-43ffc1f.52 selected source/doc files, per-file hashes in BASELINE.json. Current generated XML/Arduino were excluded from copied snapshot; read-only live evidence hashes pinned separately.
- User asked investigation only. No controller fixes, parameter edits, export/regeneration, tests, compilation, upload, deployment/restart, service calls or vehicle runs. Only audit artifacts and their entry link were written by the lead.
- User-facing report: docs/audits/2026-10-25-corner-failure-squad.zh-TW.md

## Actual workers and departments

All workers used fork_turns=none, inherited parent model, no model override. The collaboration interface does not expose the resolved model identifier, so no exact model is asserted. Three concurrent workers plus lead; six scopes completed in two rounds.

| Worker/task | Round1 | Round2 |
|---|---|---|
| /root/sense_department | A-SENSE: sensing/hardware | D-MARKER: marker/stop arbitration |
| /root/state_department | B-STATE: turn/capture/gap | E-EXPORT: Blockly/export boundary |
| /root/control_department | C-CONTROL: speed/stage | F-PROCESS: version/evidence workflow |

All prompts explicitly prohibited file mutations, tests, hardware/network/deployment/restarts/commits/other-chat messaging. A performed one additional narrow independent cross-check of lead's early-entry hypothesis.

## Accepted findings and lead verification

- BUG-01 (B): turnCandidate/candidateAt persist across active pivot and done. Verified rewrite244-245,450-456,480-485,561-610 and corresponding generated logic. Hand trace: qualified F2 enters at0, F4 capture30-45 completes, isolated F2 at50 reuses old candidate age and pivots immediately without new15ms qualification. Proposed repair deferred: consume/reset candidate per turn event.
- BUG-02 (B, output corroborated E): capture visibility computed before outer direction override (rewrite240-243,283-303; live car.ino225-234). Hand trace: right turn with prior F0, currentF2 plus newly confirmed outer-left; old predicate acceptsF2, direction switches left, then forward-right100/20 capture starts. Proposed repair deferred: finalize direction first and invalidate/requalify capture when source changes.
- R-01 (lead, cross-checked A): early F2 entry with no F0 can retain pivot until150ms and fault on still-visible F2; supported outer source can remain until800ms. Verified exact path, but classified POLICY RISK, not proven implementation bug, after A noted deliberate original-edge versus reacquired-edge distinction.
- R-02 (B): authorized disabled-loss mode renews gap and moves45/45 once120ms direction expires. Qualified as no local cumulative loss budget, not infinite operation: total180s limit remains.
- R-03 (A/B): wide observation cannot establish new outer evidence; direction expires120ms and wide command becomes100/100. Physical corner attribution unverified.
- R-04/R-05 (D): ordinary F14>=30ms -> F4 can legitimately invoke user-selected lift stop without unique physical identification; corner recovery clears only on80ms continuousF4 and can suppress later markers on valid F6/F12 indefinitely within the global run.
- R-06/R-07 (C): retained stage is not retained output. F6/F4 cycles lacking30ms centered keep actual output174 despite stored230; single F2 resets stage;30ms trim boundary can jump230/200 to174/87 or100/70 to174/87. Deterministic commands, unknown physical response, policy risks rather than arithmetic bugs.
- R-08 (D): split shared deadline, ordinary wide timeout, finish and lift are independent stop owners not bypassed by F0 flag. These are current policies, not evidence they caused the reported stop.
- Sensing (A): legacy surface labels/current track polarity, per-channel threshold contrast and sensor order need current evidence; no proven wiring inversion or F/sumW arithmetic bug.
- Export (E): no proven current import/output defect. Boolean-vs-number issue is fixed. Import/connection checks do not prove native compilation or SRAM/flash fitness; old temporal candidate native evidence is not root-car evidence.
- Process (F): incident-to-flashed-version attribution missing; repeated symptom-driven mutually incompatible hypotheses; temporal-candidate docs/capture format can be misapplied; formal release is not measured reliability baseline. Existing docs correctly acknowledge these limits; user's no-extra-tests constraint is not a defect or fault.

## Rejected, corrected and deferred claims

- Rejected as proven BUG: lead's early-entry/capture contract mismatch. Accepted reachable behavior only, preserving independent disagreement rationale.
- Corrected B wording of unlimited fallback: no per-loss cumulative limit, but global180s stop exists.
- Rejected as current root causes without evidence: old Boolean import issue, actual inverted wiring/polarity, board resource overflow, specific mechanical angle/turn radius, and claim that newest source is verified on the car.
- Did not label user-requested230/174 PWM or disabled stops themselves unauthorized bugs. Report explains their reachable consequences.
- All code fixes and policy changes deferred because request is review-only. No automatic restore of loss stops, rollback, speed changes, marker changes, new Release or snapshot-tag movement.
- Native compilation, current firmware identity, incident telemetry and field acceptance remain unverified; no request for a new driving test was executed.

## Validation and delivery

- Lead read every report, mapped snapshot lines to unchanged live source and inspected generated counterparts for primary defects.
- Verified hashes of all52 snapshot files and live generated XML/Arduino before writing audit artifacts. Recheck controller/source hashes and Git diff before final delivery.
- car.xml SHA25609b3f3bce38722ca51b2d46a20ecc0ae6c7f71421204e5deb888d735ee40aced.
- car.ino SHA256f233291b21fc6a3f0cc862188baf16ed5e90c484320c7f9c1c768c356a56ce79.
- No worker/model/tool setup failure; no substitutions. No new runtime evidence, compilation or hardware acceptance.
- Delivery: task-scoped audit commit/push on existing branch, PR6 summary updated; no merge. Local active docs receive audit report/link only. Snapshot/Release control artifacts remain unchanged.

## Recommended next work (not executed)

Fix the two implementation defects first, then define explicit approach/search/capture/wide/marker contracts and observable stop owners. Only after incident evidence is available consider sensor calibration, timing/PWM or route discrimination changes. Preserve user-selected defaults until a separately scoped strategy decision changes them.
