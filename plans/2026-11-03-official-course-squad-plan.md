# Official course simulation squad plan

Goal: continue implementing a complete-course executable model, closed-loop simulation and evidence-driven controller optimization using the confirmed November 7 designated-group official source. Preserve a strict distinction between source-verified official geometry and inferred reconstruction; never certify an unverified model as the exact official course or turn fixture records into lap evidence.

Baseline: add30a7607f220b89d2d3e015dd7475e4527c4bc; clean working tree before plan. Stable snapshot: E:/Temp/tirt-squad-20261103-add30a7, SHA manifest SNAPSHOT.json. Read-only workers; lead owns all edits and delivery.

Known facts: actual native INO/controller is available through host mocks; existing simulator only tests short synthetic planar segments. Official PDF pages5/6 provide a route illustration, T/V/shortcut/seesaw/lift, line width2cm, raw drawing labels20/19/4 with unclear units. Metric route, layer connectivity, mechanism dynamics and measured car calibration remain incomplete. The user confirmed the exact event URL. Native/core speeds and behavior may be improved only with reproduced failures and retained comparison evidence; no hardware upload or motor operation. Stable tags and root rollback INO/XML stay untouched.

| ID | model | scope | focus |
| --- | --- | --- | --- |
| A | inherited current model | official PDF/images, official_course.json, report | Recover justified route topology, directions, start/finish and drawing constraints; identify a reproducible raster/layer reconstruction method and remaining unknowns. |
| B | inherited current model | tools/simulation_model.py, physics_sim.py, tests/test_physics_sim.py | Audit integration, sensing and physical limitations; propose implementable layered surface, slopes and mechanism dynamics, with useful nontrivial tests. |
| C | inherited current model | controller.h, sim_native.py, course_qualification.py, qualification/native tests | Audit stopping/marker/search behavior and acceptance integrity; propose measurable fixes and independent trace judging. |

Workers return <=400 words in file:line | BUG/RISK/NIT | issue | concrete failing scenario | proposed fix form, plus explicit uncertainty. Snapshot line numbers only; no edits, deployment, restarts, commits, other-chat messages or subagents. Use read-only local Python/file inspection; external official rules browsing is allowed only for A if needed, no contacting organizers.

Done criteria: build a usable course model and loop integrating actual native controller, wheel/motor/sensor model and independent geometry/mechanism/finish checks; retain explicit provenance and unresolved assumptions. Run fixed, predeclared five-seed full-course attempts with failures retained; iterate on reproduced defects without weakening rules to obtain successes. Five successful inferred-model trials are distinct from official verified acceptance. Run relevant existing regression and AVR build for firmware edits. Deliver offline replay plus compact results/report, scoped commit/push and update PR6. If verified official completion cannot be established, report exact run outcomes and remaining evidence gaps without abandoning implementable work.
