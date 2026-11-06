# Two-marker practice candidate

User-requested sequence: first confirmed five-white stops for27000ms, second confirmed five-white latches finish. Derived from the runnable native motion core with its legacy marker/lap calls disabled in an isolated copy. Native rollback is unchanged. It is not the low-pass-rate layered empty-route controller and has not passed a real full lap.

Open race_two_marker.ino with its two headers, or use the dependency-free single-file package. Nano ATmega328P Old Bootloader compilation:8250bytes Flash,287bytes globals. No NeoPixel/vendor library. Compile-only; no device upload performed.

ADC physical order A5,A4,A3,A2,A1. Each Schmitt state enters white at<70 and leaves at>=100; intermediate values retain state. These provisional per-sensor thresholds require morning verification. Motion and mission consume the same canonical bits.11111 stops immediately,30ms continuous confirmation counts. During27s wait no patterns can increment the counter. Exit45/45 requires00100for100ms within1500ms before accepting a second marker; expiry wins. Finished/fault remain stopped until reset. Total run360s; scheduling gap>100ms fails. Uncertain inner patterns have800ms budget, cleared only after30ms narrow recovery; inherited split20ms failure still applies.

D12 active-low with existing external bias: release then press25ms to start. A second debounced press latches stop. No remote start. Motor pins unchanged D7/D5left,D4/D6right. Zero PWM is not a guarantee of active mechanical braking.

Rules require physical finish crossing and mechanism completely settled. Two all-white events are a user-specified course hypothesis, not a guarantee in the PDF. Verify no additional broad patches qualify, the lift is stopped at departure, and the physical timer detects finish before the car stops. Full32pattern/state analysis and final-practice checklist are under docs/race-two-marker-2026-11-06.

Packaging: `py -3.11 tools/package_race_two_marker.py --output build-output/race-two-marker-release/race_two_marker/race_two_marker.ino`.
