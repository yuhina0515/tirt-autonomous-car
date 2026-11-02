# Physics scenario simulation and gap capture priority — 2026-11-02

## Scope and authorization

The user requested scenario scripting, then explicitly required physical/machine performance consideration and attempts to improve it; later suggested checking TIRT rules for dimensions. This supersedes the previous no-extra-tests instruction for offline simulation. No upload, hardware connection or motor operation occurred. Starting HEAD46bad64, clean tracked worktree, existing PR6.

## Evidence and model

Read local official PDF physical pages3/6 with pypdf and inspected rendered page6 using the PDF skill. Rules constrain vehicle dimensions/weight/two drive wheels and specify2cm line for the3D track; no actual wheelbase, sensor pitch, loaded wheel speed or dead zone. Online PDF read failed; do not claim fresh organizer-update verification. Official CAGEBOT product154 describes a possible TR motor at4.5V/130rpm±10%/1:55, but actual installed model is unverified. Consulted primary WPILib differential-drive/feedforward and Arduino PWM documentation.

Added tools/sim_native.py: Windows/MSVC DLL executes actual exported INO with mocked Arduino GPIO/ADC/time, LED/Serial no-ops, and observer-only first fault source-line/F instrumentation. tools/physics_sim.py closes the loop with assumed geometry, sensor footprint/noise, sample/decision latency, dead zone, motor lag, coast, battery/gain asymmetry, acceleration/grip limits and planar differential drive. This is not calibrated, AVR timing/memory validation, a torque/current model, a seesaw/lift model or actual TAIWAN artwork. Road-bound excursion is reported separately from reaching an exit. All evaluated grades are zero.

## Findings and changes

- Broad exploratory48-case results favored a gentle acceleration trial41 reached vs38 current, but a132-case different-seed batch reversed that79 vs92;24/25 gentle faults were gap timeout despite valid narrow line. Do not cherry-pick the initial gain.
- Fixed cross_gap: valid narrow line captures first and confirms15ms even across the120ms lost-line deadline. F14 transfers direction/recovery; remaining invalid patterns keep the existing deadline/fallback. Fault output is guarded from later overwrite. No speed or stop-switch changes.
- Fixed132-case replay reached94 vs92 and faults5 vs7, both with14 escapes/19 timeouts and4 reached cases crossing assumed road bounds. Remaining search/F10 faults and wide-patch failures are unresolved.
- Rebuilt gentle candidate from the fixed generator:101/132 reached vs94, then new-seed88-case batch67 vs66, faults1 vs5 but escapes11 vs8. Do not adopt gentle as default: fewer faults can merely become more escapes. Keep experimental profile separate with mandatory non-root --output. Default speed100/150/190/230 remains.
- Preserve complete success/failure summaries, parameter sets, case outcomes and source hashes under docs/simulations/2026-11-02-summary.json; figures and report route through docs/PHYSICS_SIMULATION_2026-11-02.zh-TW.md. Raw traces, DLLs, compilers' intermediates, vendor assets and plotting/node packages remain ignored under build-output or external vendor directory.

## Validation and delivery

10 new checks cover model invariants and actual-sketch reset/replay, valid-side following, wide exit marker, gap120ms boundary, fault output and wide handoff. Full25-test suite passed using Python3.11. System Python3.9 initially failed two existing temporal-builder tests on unsupported Path.write_text(newline=...), resolved by using installed3.11 without editing retained temporal code. Linux CI skips the MSVC-only replay class but runs model checks.

Vendor import connection verification and Arduino export passed for main and experimental XML. Default regeneration matched active XML. Original gentle export matched570-step parameter replay before the gap fix. Source/control changes reduced generated Arduino1401→1362 lines. git diff --check passed. No Arduino target compilation, upload, vehicle acceptance, merge, Release or memory update.

Synchronize active files/current docs to E: mirror only after verifying original main files still match46bad64. Preserve old stable/snapshot files and E: unrelated staged/untracked files. Scope commit/push and update PR6. Future work should calibrate actual geometry, motor identity, PWM-to-loaded-speed/deadzone, coast and ADC polarity before any real-car performance claim; do not infer prior stable firmware failure from the uncalibrated model.
