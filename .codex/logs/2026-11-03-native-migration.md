# Independent Arduino control migration — 2026-11-03

## Authorization and baseline

User explicitly said "doit" after the proposal to retain hardware/rollback XML, create a handwritten Arduino core, preserve behavior first and compare compilation/measurement. This authorizes native-source edits and target compilation, overriding the historical generator-only rule for the new source. It does not establish an upload or hardware test. Start f3501be, clean branch docs/legacy-sensor-truth-table, existing PR6.

## Implementation

- New main source firmware/native_car/native_car.ino (69 lines) plus controller.h (353),422 total vs1362 exported lines. Pure C++ input/time→signed wheel output core, explicit Motion/Lift/Fault enums, fixed-width state, constexpr settings, common wheel helpers. No dynamic allocation/String or Arduino dependency in core.
- Standard Arduino adapter keeps physical pins/order, start button and default green/blue LED using public Adafruit_NeoPixel1.15.3. Debug defaults off and omits UART; enabled telemetry preserves A1..A5/F without String. Explicit zero output before boot button wait is an intentional startup clarification.
- Root car.xml/car.ino and tools/rewrite_car.py remain byte/content unchanged as f3501be retained reference; temporal candidates unchanged. Do not regenerate native firmware or promise reverse conversion to editable blocks.
- Extend tools/sim_native.py to compile actual native adapter/core with host mocks. Native source hash covers both INO and header. tools/physics_sim.py accepts native source/reference; native compile-time settings reject runtime parameter overrides.
- Add Compile-Native.ps1, compile only; no ports or upload. Route README/car.md/AGENTS to new source and preserve historical documentation.

## Target build evidence

Actual Arduino CLI1.5.1, AVR Boards1.8.8, avr-gcc7.3.0-atmel3.6.1-arduino7, arduino:avr:nano:cpu=atmega328old. Original vendor LED library read from installed CAGEBOT package only for baseline; proprietary source not copied into Git. Public Adafruit dependency clone pinned1.15.3/67f2ed09e9dd755ab1f606ec5940c50af52afae3 remains ignored.

- Original exported/vendor LED: Flash17982, static global RAM801.
- Exported with same public LED library:17072/689.
- Native default LED on/debug off:8662/203.
- Native LED on/debug on:10146/386.

Defaults reduce Flash51.8% and global RAM74.7% vs original, or49.3%/70.5% vs same-LED control. These are whole-build comparisons, not peak memory or loop-cycle measurements. Native HEX and sources are indexed in docs/native-build-2026-11-03.json.

## Validation

29 Python tests passed on3.11 including four new differential groups (timed phases/thresholds, outer confirmation/probe, millis wrap/overall deadline,100 seeded mixed episodes). Windows MSVC executes both actual adapters; source-line fault observer is excluded from parity, fault F retained. Standalone C++ core assertions passed locally and were added as a C++11 Linux CI step. Platform skips are explicit; CI result is separate from local checks.

Final132-case same-plant comparison: both94 reached/5 fault/14 escape/19 timeout,4 reached-with-road-excursion. All case metrics and final observable states matched.11 nominal traces/5541 rows matched except firstFaultLine. Native bundle57c856389b5a1a168079da527805a061fc0e900dfe4bfb55fc41379f2a9baf9a. Raw traces and binaries remain ignored; compact evidence saved under docs/simulations/2026-11-03-native-migration.json. No source/field success inference from these uncalibrated outcomes.

## Delivery and limits

Mirror source folder and current docs to E:/Projects/XiangyiRobotDreamFactory/self-driving_car; retain root XML/INO and snapshots. Local native-build holds application HEX and build manifest, not bootloader HEX. Scoped commit/push and update PR6; no merge/tag/Release or memory update.

No upload, device connection, motor operation, actual bootloader identification, loop timing, peak RAM or driving acceptance. Known sensing/marker ambiguity,180s/long-wide behavior, lift23.35s and finish-exit requirement remain. Stage/curve/search speeds are unchanged. Do not call resource reduction a solved TAIWAN turn or a measured vehicle speed improvement.
