# Project working rules

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
