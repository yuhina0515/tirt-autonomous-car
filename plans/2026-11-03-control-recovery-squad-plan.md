# Squad control and physical recovery continuation

Goal: continue toward five consecutive complete-course runs by improving the actual controller and resolving physically important model assumptions, while retaining independent judging and the official-source verification boundary. Deliver a tested experimental controller if mainline promotion is not supported; do not merely repeat prior audits.

Baseline a78eebe1e1c46068c0a381f1f2f01fd645e33a6c, clean. Source snapshot E:/Temp/tirt-squad-20261103-control-recovery-a78eebe. Existing immutable evidence: C:/Users/Yuhina/Documents/Codex/2026-10-24/tirt/team-repo/build-output/full-course/current-final and experiment-05, including frozen manifests, sources and5ms traces. Generated evidence is referenced read-only rather than duplicated into source snapshot.

Known facts: source diagram traversal211vertices/209gates, unverified metric/direction/layer configuration; fifteen prior runs failed, maximum75gates. Three high-torque cases remain on F8 during uphill capture then hit800ms; one cross near unresolved F is falsely treated as lift although all five ADCs are low; one loses road. Capture150/lift29/deadline360 experiment did not finish. Original2.5m/s2 motor hypothesis is infeasible on some assumed slopes;6m/s2 used for comparison remains uncalibrated. Native main now only fixes stale continuous dropout timer. Hardware-only input remains ADC/time; no pose/gate/world oracle. Preserve original rollback XML/INO, stable refs, Bluetooth scope and no hardware operation.

Training retains seeds2026110701..705. Held-out seeds2026110711..715 are declared in simulation/recovery_validation_seeds.json before candidate tuning; successes from separate versions/plans cannot be combined. Short diagnostic-budget probes are explicitly excluded from five-run qualification.

| ID | model | scope | focus |
| --- | --- | --- | --- |
| A | inherited current model | native core and failure ADC/command traces | Continuous sensor-position PD/PI, preview, motor load and bounded recovery; concrete candidate design grounded in observed failures. |
| B | inherited current model | course_world, simulation_model, reconstructed course | Force/backdrive/friction/caster and uncertain crossing hypotheses; material model corrections and physically declared sensitivity ranges, without easing legal checks. |
| C | inherited current model | referee/runner/auditor and sensor-event mission design | Independent acceptance integrity, observation aliasing and allowable onboard route/event sequencing; no true-position input to control. |

Read-only workers: no writes, deployments, restarts, commits, hardware, external messages or subagents. Return<=400words file:line | BUG/RISK/NIT | issue | concrete failure | proposed fix, with verified findings and explicit uncertainty. Source lines refer to snapshot; immutable CSV evidence may be cited by path/row. Only lead edits and integrates.

Done criteria: reproduce failure causes; implement and compile an improved actual Arduino experimental core with continuous line position/control and bounded uncertainty as justified; maintain marker ambiguity rather than assert perfect rejection. Run predeclared five-seed batches and directed physical/controller regressions under unchanged legal checks, retain failures and compare held-out conditions. Freeze all config/code/evidence, verify ADC-origin and actual core replay, produce replay and concise English handoff/Traditional-Chinese report. Mainline changes require demonstrated benefit and preserved limitations. Exact official five-run acceptance remains blocked by unverified source geometry/calibration; report model completions separately. Task-scoped commit/push/update PR6; never merge or upload.

Final review snapshot: E:/Temp/tirt-control-recovery-review-20261103-v2 (43 relevant files plus diff and hash manifest). Workers retained inherited model; no model overrides or read-write delegation.

Review follow-up: reproduce the118/137 opposing-occurrence switch using ordered referee progress; reject station-only training label forgery using audited pose and preceding gates. Regenerate training after split-confidence/corner-guard fixes. A later post-lift motor-only revision may reuse a training prefix only after exact revised-core command/state/event replay from regenerated physical ADC through every audited target; staging still binds the complete revised source identity. All post-lift driving requires fresh trials. Preserve failed/aborted diagnostic evidence.
