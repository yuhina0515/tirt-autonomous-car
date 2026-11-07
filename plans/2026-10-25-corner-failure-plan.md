# Corner Failure Squad Audit — 2026-10-25

## Goal and scope

Explain why the current TIRT car repeatedly stops, runs straight out of60/90-degree corners, or overshoots. This is an explicit review-only root-cause request: do not change controller behavior, parameters, XML, Arduino, firmware, released assets or hardware. The lead may write the plan/reports/handoff and deliver them through the existing branch/PR. No driving tests, uploads, native compilation or added automated tests. Static code paths and hand-traced sensor sequences are allowed as reasoning, not measured validation.

## Baseline and evidence

- Repository: C:/Users/Yuhina/Documents/Codex/2026-10-24/tirt/team-repo
- Baseline HEAD43ffc1fbb8f16ad750393f13d886401f97891246, clean working tree before plan. Control files equal434af1d. Branch docs/legacy-sensor-truth-table; v0.4.0/e19e214 is published formal baseline, not proof of hardware stability.
- Read-only source snapshot: C:\Users\Yuhina\Documents\Codex\2026-10-24\tirt\audit-snapshots\2026-10-25-corner-failure-43ffc1f
- BASELINE.json records every copied file hash and live generated XML/Arduino hashes. Generated current files are intentionally excluded from the snapshot; inspect live car.ino/car.xml read-only only if needed and label those citations as live generated evidence. Report primary findings against snapshot source lines; lead verifies mapping/hashes before finalizing.
- User repeatedly reported physical white surface at folds, side line visible after forward motion, right60-degree runout and past wrong-side/overrotation. No incident rawADC/F trace or verified current device firmware. Never equate physical white with F0/F14 without evidence.
- Current center F uses ADC<70, sides A5/A1 assist. Straight230, curve174, search150/-114. LOSS_STOP_ENABLED0 and CORNER_WIDE_STOP_ENABLED0 are user-authorized; do not silently restore them. Lift is qualified F14->F4 exit with23.35s wait. Prior changes evolved over23 tuning commits.
- Static shell/file tools are available. Use local Git history only; no remote system fetch/deployment or connected messaging. All workers are read-only: no file edits, deployment, service restart, commit or other-chat messages.

## Departments and schedule

Maximum four concurrent agents including lead; launch three independent readers, then queue the other three using idle workers. All use inherited parent model with no override; resolved model identifier is not exposed by the spawn interface. Record actual worker IDs in handoff.

| ID | Model | Scope | Focus |
|---|---|---|---|
| A-SENSE | inherited, no override | hardware.md; docs sensor/field policy; rewrite_car.py final rewrite/normal-F construction | calibration/polarity/observability and motor/wiring evidence |
| B-STATE | inherited, no override | rewrite_car.py add_sharp_turns pivot/capture/gap, roughly lines190-355 | reachable state transitions, deadlines, dropout/fallback and wrong direction |
| C-CONTROL | inherited, no override | rewrite_car.py setup settings, straight_update and replace_normal_follow | stage resets, actual wheel commands, turning authority and open-loop PWM limits |
| D-MARKER | inherited, no override | rewrite_car.py lift_update/lap_update/normal wrapper/split/corner-wide update | false lift/finish, stopping arbitration and suppressed markers |
| E-EXPORT | inherited, no override | blockly_codegen.py, tools/export_car.mjs, XML ID construction/export boundary | block validity, source/output semantic mismatch, unsupported native-size claims |
| F-PROCESS | inherited, no override | current docs, local Git evolution versus v0.4.0; evidence/acceptance workflow | contradictory fixes, causal claims without traces, comparison limits and minimum decision gates |

## Report format

Each report: at most400 words, up to five findings. Format each: `file:line | BUG/RISK/NIT | issue | concrete failing scenario | proposed fix`. Distinguish proven reachable code behavior from possible physical cause. Include trigger F/timestamps and commands where possible, severity, uncertainty, and one useful next diagnostic. Report no finding rather than inventing. Do not conflate generic caution with bugs.

## Lead verification and done criteria

Launch independent workers before examining their reports. Verify claimed bugs in current source against pinned snapshot/live hashes; hand-trace a minimal sequence when useful. Record accepted, rejected and deferred claims and overlaps. No fixes for this review-only request. Deliver a Traditional Chinese synthesis with ranked causes, certainty, and a bounded remediation order; English plan/handoff logs record actual agents, failures/limitations and native acceptance outstanding. Write .codex/logs/2026-10-25-squad-corner-failure.md and update .codex/logs/INDEX.md; retain a user-facing audit report under docs/. Preserve snapshot tag and formal Release. Confirm control hashes unchanged at end.
