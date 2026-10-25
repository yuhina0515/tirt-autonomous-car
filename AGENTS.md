# Project working rules

## Active baseline after user-directed rollback (2026-10-25)

- After the section4 push/runaway report, docs/RUNAWAY_FIX_2026-10-25.zh-TW.md is authoritative: confirmation restored15ms; only explicit F4 ramps from125 to230 after80ms centered, steps10 per10ms. F10/unexpected normal patterns latch stop; use F-based turn conditions instead of strict >70 ADC branches. No-direction gaps are45/max120ms. These override earlier1ms/gap70 notes below; no field acceptance claim.
- For reported detection lag, root car.xml now defaults DEBUG_SERIAL=0; optional telemetry period50ms, LEDs update only on state transitions, and turn/gap reacquisition uses continuous1ms instead of3 loops. Read docs/CONTROL_LOOP.zh-TW.md. No measured sampling-rate claim or new hardware acceptance is available.
- Straight PWM230 remains user-authorized. After the user reported excessive turning, active root car.xml reduces curve base to125, TURN_KP100, minimum inner8 (actual25/75), sharp outer125/reverse inner95; see docs/SPEED_SETTINGS.zh-TW.md. This overrides the default100 cap for these commands. Gap70 and wide/lift-exit45 remain. Preserve published v0.4.0 assets/tag; do not claim new field acceptance.
- The appended lift candidate is documented in docs/LIFT.zh-TW.md. User tentatively reports no prior crossings: LIFT_ENABLED=1, crossing index1. The user requested reducing the wait from28350ms to23350ms for v0.4.0; it is below the published27s +/-5% timing. These are assumptions, not measured descent completion; do not claim compliance or unique recognition. Disable lift for the prior practice mat without it.
- Before competition-strategy changes, read docs/TIRT_RULES_2026.zh-TW.md and distinguish official requirements from practice-mat assumptions and local controller parameters. The documented rules do not imply that the current firmware completes the official course.
- Root car.xml and car.ino are the active rewrite of the three-center-sensor PWM100 baseline from self-driving_car. Read README.md, car.md and docs/SENSOR_TRUTH_TABLE.zh-TW.md before strategy changes. tools/rewrite_car.py rebuilds XML from the preserved legacy source; tools/export_car.mjs exports it with local vendor generators. Legacy files remain unchanged.
- Later user-authorized additions are documented in docs/SHARP_TURNS.zh-TW.md and docs/ONE_LAP.zh-TW.md. Start is the narrow line left of the large finish patch, not the patch itself. Minimum runtime/wide-duration finish detection is a candidate, not proof of a full lap; no new tests or upload have been performed.
- The user requested removal of today's controller experiments and restoration of the original strategy. Preserve its behavior until a concrete strategy change is specified.
- For this baseline edit CAGEBOT XML and export Arduino from that XML. build.py/config.json only own the retained temporal candidate under firmware/, not root car.xml.
- The user requested no additional testing for this rollback. No tests or upload were run; do not imply new hardware acceptance.
- The temporal-controller rules below apply to that retained candidate.

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
