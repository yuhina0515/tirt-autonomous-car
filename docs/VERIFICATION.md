# Verification and acceptance boundary

Checked on 2026-10-24 before public publication. No vehicle was available for
this controller version, and no hardware upload or real track test was performed.

| Check | Result |
|---|---|
| Python unit tests | 7 tests pass: configuration rejection, current generated exports, unknown-block rejection, labelled calibration, data ranges and clock reset/wrap |
| Native track controller | 6143 assertions, trace `7e3247dc`, 32-bit long |
| Native motor-off capture | 1952 assertions, trace `17512a2b`, 32-bit long |
| Real CAGEBOT XML import | Both profiles pass with 1270 / 1222 instantiated blocks |
| Real CAGEBOT Arduino export execution | Same assertions and trace hashes as local exports |
| CAGEBOT save/reload | Both saved XML files export byte-identical local Arduino |
| Local and vendor AVR track compile | 12054 bytes flash, 570 bytes RAM |
| Local and vendor AVR capture compile | 7984 bytes flash, 438 bytes RAM |
| PowerShell receiver/launcher | Syntax parser passes; native COM reception with this new CSV contract still needs field acceptance |

AVR target: `arduino:avr:nano:cpu=atmega328old`, Arduino AVR core 1.8.8.
The new profiles require only the Arduino core, not proprietary extra libraries.
Vendor generator JavaScript is not distributed; its verification hashes are in
`verification.json`. Vendor checking script accepts separately acquired files.

Native tests execute the actual generated C++ with fake ADC/time/PWM I/O. They
cover unarmed/held button, continuous acquisition, transient wide/side patterns,
loss/split/wide deadlines, alternating interference and valid blips, outer-input
invariance, mirrored steering, mixed calibration polarity, timing faults, manual
stop, run limit, saturated ADC and millis rollover. Rollover checks require a
32-bit unsigned long; GitHub CI builds with `-m32` for that reason.

These tests cannot establish motor response, sensor geometry, camera ground
truth, radio reliability, stopping distance, or whether a particular white word
will produce a trusted-looking sensor sequence. A persistent narrow white mark
can pass the confirmation rules. No perfect text immunity is claimed.

Re-run `python -m unittest discover -s tests -v` after changes. Linux native checks:

```sh
mkdir -p test-output
g++ -m32 -std=c++17 -I tests tests/native.cpp -o test-output/track
test-output/track
g++ -m32 -std=c++17 -I tests -DCAPTURE_TEST '-DSKETCH_FILE="../firmware/stationary_capture/stationary_capture.ino"' tests/native.cpp -o test-output/capture
test-output/capture
```

For separately downloaded CAGEBOT JavaScript and Playwright, the vendor check is:

```text
node tests/verify_vendor.mjs <playwright/index.mjs> <vendor-js-directory> <profile.xml> <output.ino>
```

Compare native traces and compile the actual vendor export, not only the local
translation. Field data must reference the exact flashed source/manifest.
