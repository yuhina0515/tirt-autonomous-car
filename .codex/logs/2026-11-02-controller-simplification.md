# Controller simplification — 2026-11-02

User authorized simplifying the active controller after reporting that the car stopped with all three center sensors still over white at a TAIWAN60-degree corner. This confirms resting position, not elapsed time, F value, firmware identity or stop owner.

Baseline HEAD336e17c, controller434af1d, clean branch docs/legacy-sensor-truth-table, existing PR6. Preserve stable tags and previous snapshots. No subagent delegation or memory update.

Changes: remove six visible-side early pivot entries,150ms unsupported-search fault and900ms ordinary-wide fault. Only F0 starts search. One wide-to-centered exit observer handles lift/finish; finish now requires exit F4 after250ms wide and minimum15s/lift complete. No narrow finish exit means no marker finish stop. Consume candidates on entry/completion/fallback; latest capture side wins in fallback; select direction before capture qualification and forbid override after capture starts. Transfer gap direction/recovery on F14. Factor repeated fallback blocks into one vendor-generated procedure; remove unreachable completion subbranches and unused wide timing variables. Speeds, disabled loss-stop switches, split/probe behavior, lift wait/exit,800ms search limit and180s overall deadline remain.

Validation: Python generator completed; saved CAGEBOT generators imported XML with parent-connection checks and exported Arduino successfully. Inspected generated search entries, ordering, fallback, marker exits and stop paths. git diff --check passed. Arduino output1656→1401 lines. Runtime npm packages are ignored under build-output/export-runtime; proprietary vendor assets remain outside Git. No added/running tests, simulation, Arduino compilation, upload or field run under existing no-extra-tests instruction.

Delivery: synchronize exact active XML/INO and current docs to E:/Projects/XiangyiRobotDreamFactory/self-driving_car, preserving old snapshots. Commit scoped paths, push branch and update PR6 without merge or Release. User-facing entry docs/SIMPLIFICATION_2026-11-02.zh-TW.md. Current firmware remains unknown; do not report successful corner/lap acceptance.

Risks: persistent F14 can proceed until180s; identical unqualified F14→F4 observations may still misidentify a corner as a marker. Finish placement changes to the centered exit. PWM values are not measured speed, physical white/F polarity is unverified for the event, lift23350ms has the existing timing/feedback limitation. Actual stop root cause is unproven.
