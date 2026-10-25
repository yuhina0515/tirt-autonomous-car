# Project working rules

## Current source snapshot (2026-10-25)

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
