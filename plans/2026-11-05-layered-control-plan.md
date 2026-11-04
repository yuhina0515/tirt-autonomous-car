# Layered race controller plan

## Goal and authorization
Preserve the runnable native firmware as rollback. Build a separate, simpler controller with a sensing/motion layer and an explicit race mission layer. The user authorizes redesign, automatic tests and plan updates. The 23350 ms lift wait is an intentional Xiangyi field setting, not an accidental rule mismatch. Keep it selectable; do not claim the mechanism has settled from elapsed time alone.

## Baseline and scope
Repository: team-repo, branch docs/legacy-sensor-truth-table, clean before this task. Snapshot: E:/Temp/tirt-layered-20261105-baseline (native_car and candidate_car). Record baseline revision in handoff. Root rollback XML/INO and native_car remain unchanged. Do not deploy a new experimental firmware over the working Hina Web download automatically. No device upload/motor operation. No model coordinates or referee progress supplied to firmware.

## Task table
ID | model | scope | focus
---|---|---|---
A | inherited | native_car controller and adapter snapshot | Minimal separation, hazards, unnecessary test-track assumptions
B | inherited | candidate_car snapshot, current tests and official_course.json | Reusable sensing, measurable race mission contract, focused tests
Lead | inherited | implementation, validation, Git delivery | One owner; no parallel edits; bounded test runs

Workers are read-only: no edits, deployment, commits or messages to other chats. Reports <=400 words, file:line | BUG/RISK/NIT | issue | scenario | fix. Identify unknown route and mechanism inputs explicitly.

## Implementation sequence
1. Freeze source and inspect independent reports.
2. Add firmware/layered_car, with a pure observation/motion controller and mission controller; explicit route instructions rather than broad-white counting or model-trained mission words.
3. Separate field lift timing from race conservative timing. Gate actual lift/finish decisions on a configured route; an empty route is line practice, never a claim of race navigation.
4. Directed tests for line following, bounded dropout/wide/split ambiguity, direction at junctions, lift wait/rearm, finish and time rollover. Compile Nano old bootloader. Retain evidence of incomplete route calibration and field acceptance.
5. Commit task-only files, push and update existing PR 6, no merge. Write concise handoff and next hardware inputs.

## Done criteria
- Baseline native/rollback hashes unchanged.
- New core has independent motion and mission contracts, no hidden geometry oracle, and explicit profiles.
- Focused tests, existing suite and Nano compile pass or failures are diagnosed.
- Unknown official route/marker uniqueness and absence of settled feedback are documented; no completion claim from unit tests or the unverified course model.
- Reviewable task-scoped delivery and handoff.

## Execution update
- Fast-forwarded clean source from bcd5e68 to 0fc45e6 before implementation, preserving 11/4 ground/junction work and all reserved seeds. Native snapshot source hashes remain identical.
- Both read-only audits accepted separation; implicit first-wide lift, repeated loss fallback and branch choice from recent error are removed in the independent controller. No edits to native/rollback controls.
- Native snapshot now also preserved in tracked snapshots/2026-11-05-runnable-native with source and prior distributed-file hashes.
- Implementation uses per-channel normalized PD, observed Wide/Split steps, chosen-side then central turn return, bounded ambiguity, configured lift/finish, and debounced run/stop. Default no-route practice is explicit. Profiles: intentional field23350ms; conservative28850ms plus ready input, unavailable in current adapter.
- Post-implementation reviews found signed/unsigned derivative, deadline-order and false turn-return bugs. Lead fixed them and added directed regressions; initial compiler setup failure was quoted Windows PATH, fixed process-locally. Two initial tests wrongly expected an exhausted non-finish route to keep cruising; fixtures now include a next step. Derivative test was extended past acceleration saturation to expose direction correctly.
- No inferred-course seed search: component tests and real Nano compilation cover this architectural change economically. Route geometry, event uniqueness, mechanism feedback, shortcut boundary and car clearance remain required field inputs for a race preset.
