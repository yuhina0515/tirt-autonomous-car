# Project working rules

## Current native control source (2026-11-03)

- User explicitly authorized moving to handwritten Arduino C++ while retaining hardware and rollback XML. This supersedes the old rule requiring all control edits to originate in the Blockly generator.
- Main source: firmware/native_car/native_car.ino plus controller.h. Read its README and docs/NATIVE_MIGRATION_2026-11-03.zh-TW.md first. Core is independent of Arduino/vendor I/O; adapter uses public Adafruit_NeoPixel1.15.3. Do not hand-sync native changes into XML or promise reverse conversion.
- Root car.xml/car.ino are preserved f3501be reference/rollback files. tools/rewrite_car.py/export_car.mjs only maintain that retained reference; build.py/config.json and the temporal candidates remain separate. Never regenerate over native_car.
- Preserve current speeds, sensor roles, switch settings and phase semantics until a scoped behavior change is requested. Refactor parity is checked through actual exported-sketch vs native-adapter command/state replay, including raw ADC thresholds and millis rollover.
- Nano old-bootloader target compilation passed using AVR Boards1.8.8/CLI1.5.1. Default native Flash8662/global RAM203 vs original17982/801; same-LED-library baseline17072/689. Defaults LED on/serial debug off; these are static build measurements, not peak RAM or measured loop speed.
- Compile helper tools/Compile-Native.ps1 never uploads. No hardware upload/operation or real-car acceptance occurred. Preserve existing physical/sensing/marker/lift limitations; model success is not field acceptance.
- tools/sim_native.py supports both exported sketches and the native adapter/core. Native hash bundles INO and header; parameter overrides are not supported for native compile-time settings. Windows parity tests and pure C++ core CI complement the uncalibrated physics comparison. Keep dependencies, binaries, raw traces and vendor files ignored.
- Keep task-scoped commits/push and update existing PR6; never merge, force-push, replace stable tags, or modify unrelated work. Bluetooth remains parked.

## Historical exported candidate (2026-11-02)

The following describes the preserved exported reference and does not override native-source maintenance above.

- Latest follow-up: docs/PHYSICS_SIMULATION_2026-11-02.zh-TW.md. User explicitly authorized offline scenario/physics simulation in chat, superseding the earlier no-additional-tests restriction for this scope. No hardware upload or motor operation is authorized/performed by this simulation task.
- cross_gap now prioritizes valid narrow-line capture over the120ms lost-line deadline, confirms continuously15ms, and guards motor output after faults. Speeds remain100/150/190/230. Compared with46bad64 in132 synthetic cases, reached92→94, faults7→5; four reached cases per version still crossed assumed road bounds. These are uncalibrated model outcomes, not real-car probabilities or legal laps.
- tools/sim_native.py compiles the actual vendor-exported INO into a Windows/MSVC DLL with mocked Arduino I/O and observer-only first-fault line/F capture. tools/physics_sim.py couples it to an assumed planar plant; tests/test_physics_sim.py has10 checks. Do not equate host compilation with AVR compilation or calibrated dynamics.
- rewrite_car.py defaults to the unchanged speed profile. Experimental gentle profile requires a separate --output; it failed a different-seed comparison before the gap fix and is not a recommended preset. Do not replace measured evidence with its exploratory result. Runtime/vendor/raw traces remain outside Git; compact summary and figure are under docs/simulations.

- Read docs/SIMPLIFICATION_2026-11-02.zh-TW.md, README.md and car.md first. Root car.xml/car.ino now contain an unvalidated simplified candidate based on434af1d. Prior10/25-26 reports are historical.
- Visible side lines follow forward; only F0 starts search. The six early side-line pivot entries and150ms unsupported-search fault are removed. The800ms search deadline remains;150ms only limits pre-capture outer direction correction.
- Ordinary F14 has no900ms stop deadline. Lift and finish share one wide-to-F4 exit observer with no turn evidence. Finish moved from within wide to its centered exit: wide at least250ms, minimum15s run, lift complete. No centered line after finish means no marker finish stop. Lift30ms/wait23350ms/exit45/exit timeout1500ms remain.
- One loss_fallback procedure replaces inline copies. Latest captureSide wins during capture, including0; candidate state is consumed at entry/completion/fallback. Direction is selected before capture eligibility; no override after capture starts. Gap-to-F14 preserves direction and recovery.
- Keep speed values, center/outer sensor roles, disabled stop switches, split/probe handling and180s overall deadline. Long F14 can now traverse until the overall deadline. No unique marker recognition, competition readiness, physical color/F mapping or hardware upload claim.
- Modify tools/rewrite_car.py then regenerate XML and export with tools/export_car.mjs and saved vendor generators. Never hand-edit only INO. build.py/config.json/firmware remain the separate retained temporal candidate.
- Vendor import parent-connection checks and Arduino export passed. The initial simplification had no extra tests; the later user-authorized offline simulation added host tests only. No Arduino target compilation, upload or driving. Never substitute export or host simulation for hardware acceptance.
- Keep task-scoped commits/push and update existing PR; do not merge, force-push or change stable tags. Keep captures, vendor files and local runtime outside Git. Bluetooth work remains parked.

## Historical source snapshot (control2026-10-25; handoff2026-10-26)

The following records the predecessor and does not override the current candidate above.

- Latest handoff: docs/PROJECT_SUMMARY_2026-10-26.zh-TW.md; snapshot/2026-10-26-reviewed-state stores latest audit data. Three confirmed bugs remain unfixed: stale candidate reuse, capture fallback uses old turn direction, capture eligibility before direction override. Archival task changes no control files or parameters.
- Read README.md, car.md and docs/CURRENT_STATE_2026-10-25.zh-TW.md before changes. Current control source is434af1d, on docs/legacy-sensor-truth-table, PR6. snapshot/2026-10-25-wide-visible-line is an archived development snapshot, not a new stable Release. Latest formal Release remains v0.4.0/e19e214; preserve its tag/assets. Older tuning docs and docs/history are historical and may contain superseded values.
- Root car.xml/car.ino are active. Change tools/rewrite_car.py and regenerate XML, then tools/export_car.mjs with saved vendor generators. Export waits for Blockly events and rejects detached parent connections. Never compare a Boolean block with numeric0; use integer flag or compatible Boolean input. build.py/config.json/firmware own a separate retained temporal candidate.
- Normal F and sumW use A4/A3/A2. User explicitly authorized raw A5/A1 corner-direction assistance:20ms confirmation,120ms memory. F bit coding is low ADC<70, not a verified physical black/white label; no perfect line/text/marker distinction claim.
- Straight stages100/150/190/230 at accumulated centered0/200/500/900ms. Mild F6/F12 trim uses stage-minus30 and pauses stage accumulation. After30ms use ordinary curve without losing stage; centered30ms restores it. Curve base/gain174, inner15/87; pivot150/-114, capture100 with inner20/50. PWM230 ceiling is user-authorized, overriding old default100 for this active program.
- Wide corner with qualified history drives forward100/50 or mirror, then100/100 after direction expiry. Visible side-line exit uses ordinary curve and skips early reverse entry during wide recovery; F0 may invoke existing search. No F14 pivot or obsolete90ms reverse strategy. Active-turn pre-capture F14 also drives forward. Centered80ms outside turn/gap clears recovery; recovery suppresses lift/finish/wide-timeout reuse.
- LOSS_STOP_ENABLED0 and CORNER_WIDE_STOP_ENABLED0 temporarily bypass corresponding F0/corner-F14 latching faults to low-speed forward fallback. Qualified right45/15, left15/45, unknown/expired45/45;120ms direction lifetime never refreshed by mere gap renewal. Other faults, lift/finish and180s total deadline remain. Do not restore stops or change these defaults without a user-scoped reason.
- Lift marker: F14 continuous30ms arms only; first non-wide must be centeredF4/no outer turn hints to stop immediately. Side/loss/split/turn/gap or wide recovery cancels. Narrow100ms re-arms. Wait23350ms then exit45,1500ms exit limit. Timing below official27s +/-5% and no settled feedback; no compliance/unique-marker/position claim.
- User requested no additional tests for this active rollback/tuning workflow. Latest source passed vendor import connection integrity and Arduino export; no new compilation/upload/driving acceptance. Source state is not current car firmware. For this documentation snapshot only refs/hashes were inspected, control files unchanged.
- Keep task-scoped commits/push and existing PR updated, do not merge or force-push. Keep proprietary vendor files, captures and local secrets outside Git/archives. Bluetooth reconnection remains parked.

## Historical temporal candidate rules (not the root-car workflow)

The following retained rules apply only to the older temporal candidate. They do not override the active user-authorized source/settings above.

- Use Traditional Chinese for teammate guidance; code, logs and commits use English.
- Change behavior in build.py and parameters in config JSON; regenerate XML and
  Arduino together. Both must describe the same program. Never promise arbitrary
  handwritten C++ can be reverse-converted into CAGEBOT blocks.
- Center A4/A3/A2 control only. A5/A1 are recorded but excluded from control unless
  the user explicitly changes the experiment. Keep PWM <=100 by default.
- Preserve existing hardware baseline in legacy. New source is not proof of a
  hardware upload; record actual upload/version and test status separately.
- Do not replace temporal confidence with a static F-to-PWM truth table. Unknown
  observations share one bounded uncertainty timer; valid blips must not reset it.
- Keep capture mode motor-off, uncalibrated track mode unarmed, held-at-boot button
  unable to start, and fault recovery manual. Do not imply PWM=0 is active braking.
- Never claim perfect white-text rejection, measured geometry, race readiness, or
  immunity based solely on unit tests or simulated sensor sequences.
- Run unit tests and native track/capture regressions for controller changes.
  Compile both profiles for Nano old bootloader. For export changes additionally
  compare actual CAGEBOT vendor output traces and XML-resave roundtrips.
- Do not publish credentials, raw personal logs, device addresses, registration
  details, editor installers, or proprietary vendor files. captures/ stays ignored.
