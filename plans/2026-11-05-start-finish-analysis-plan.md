# Start-to-finish scenario analysis and actual firmware lap

Goal: enumerate every directed segment of the existing complete illustrated-course hypothesis, associate terrain/paint/turn/mechanism hazards with executable strategies, then simulate one entire start-to-finish attempt and preserve trace/replay/audits.

Baseline:20538be. Native rollback and new layered firmware remain unchanged. Geometry, support and high-torque plant are explicitly inferred. Use known diagnostic seed2026110711 once, with unchanged ground-course and matching junction-context profile, as the current full-route strategy reference. This is not unseen validation. Reserved741..745 remain untouched. The new layered default has no route; test its actual core against the same world separately and report its failure honestly rather than equating reference completion with layered completion.

Tasks | owner | scope
---|---|---
Scenario catalogue | lead | every segment, bends, layered overlaps, paint, shortcut choice, seesaw/lift and finish
Independent route review | inherited read-only agent | source-rule versus inferred-route boundaries and strategy coverage, <=400words
Actual runs/audit | lead | one reference complete-lap diagnostic, one layered diagnostic, full physical/core checks and replay
Delivery | lead | reviewable reports, reproducible tools, focused tests, task-only commit/push/PR6 update

Snapshot: each run freezes course, firmware/model sources, plant, seed and trace; no overwrites of old batches. Worker is read-only, no edits/deploy/restarts/commits/messages to other chats. No coordinate/referee information fed to firmware; route positions are analyst/court data only. Keep field23350ms setting intact; reference model uses its existing bound31s lift strategy for27s mechanisms. Report both explicitly.

Done: complete segment catalogue, fresh measured run result (success or first failure), independently checked trace and actual-core replay, local replay and concise report with qualification limitations. No on-car or production deployment.

## Execution result

- Catalogue covers all210 directed segments in10 contiguous phases; geometry identity is pinned and4 new regression tests pass.
- Reference known711:209/209,219.320s simulation,218.880s start-to-finish. All10 attempt checks plus physical ADC, actual-core replay and independent frozen-source audit pass. One known diagnostic is not five-run/unseen qualification.
- Actual layered empty-route core, identical world/seed/plant/lift duration:82/209,Signal fault at103.305s. Replay and sensor-origin verification pass; route completion does not. Firmware remains unchanged.
- Complete local suite143/143 passes. Independent read-only final review found no blocking issues.
- Deliverables: docs/start-finish-2026-11-05/REPORT.zh-TW.md, complete catalogue/figure/receipts, two local interactive replays, reproducible tools and this handoff. Reserved741..745 untouched; no production or device operation.
